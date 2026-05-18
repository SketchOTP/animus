"""Call Hermes gateway (OpenAI server, port 8642) and optional Hermes dashboard (9119) from ANIMUS."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import httpx

try:
    import websockets
except ImportError:  # pragma: no cover - optional until pip install
    websockets = None  # type: ignore[assignment]

from hermes_runner import chat_data_dir, gateway_upstream_headers

log = logging.getLogger("animus.hermes_service")

_CHAT_PKG = Path(__file__).resolve().parent
_REPO_ROOT = _CHAT_PKG.parent
_DASHBOARD_TOKEN_CFG_MTIME: float | None = None
_DASHBOARD_TOKEN_CFG_VALUE: str = ""


def invalidate_dashboard_token_config_cache() -> None:
    """Call after writing ``hermes_dashboard_session_token`` in ``config.json`` so the next lookup re-reads."""
    global _DASHBOARD_TOKEN_CFG_MTIME, _DASHBOARD_TOKEN_CFG_VALUE
    _DASHBOARD_TOKEN_CFG_MTIME = None
    _DASHBOARD_TOKEN_CFG_VALUE = ""


def _parse_env_file_for_key(path: Path, key: str) -> str:
    """Read ``KEY=value`` from a dotenv-style file (no shell expansion)."""
    if not path.is_file():
        return ""
    key_eq = f"{key}="
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if not line.startswith(key_eq):
                continue
            val = line[len(key_eq) :].strip()
            if val.startswith('"') and val.endswith('"') and len(val) >= 2:
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'") and len(val) >= 2:
                val = val[1:-1]
            return val.strip()
    except OSError:
        return ""
    return ""


def _dashboard_token_from_chat_config() -> str:
    """``config.json`` key ``hermes_dashboard_session_token`` (server-only; not in ``ui_settings``)."""
    global _DASHBOARD_TOKEN_CFG_MTIME, _DASHBOARD_TOKEN_CFG_VALUE
    try:
        p = chat_data_dir() / "config.json"
        if not p.is_file():
            return ""
        mtime = p.stat().st_mtime
        if _DASHBOARD_TOKEN_CFG_MTIME == mtime:
            return _DASHBOARD_TOKEN_CFG_VALUE
        data = json.loads(p.read_text(encoding="utf-8"))
        tok = ""
        if isinstance(data, dict):
            tok = str(data.get("hermes_dashboard_session_token") or "").strip()
        _DASHBOARD_TOKEN_CFG_MTIME = mtime
        _DASHBOARD_TOKEN_CFG_VALUE = tok
        return tok
    except (OSError, TypeError, ValueError):
        return ""


def hermes_api_base() -> str:
    return (os.environ.get("HERMES_API_URL") or "http://127.0.0.1:8642").strip().rstrip("/")


def hermes_dashboard_base() -> str:
    return (os.environ.get("HERMES_DASHBOARD_URL") or "http://127.0.0.1:9119").strip().rstrip("/")


def hermes_dashboard_session_token() -> str:
    """Resolve dashboard session token for ``/api/ws`` and gated REST.

    Order: process env → repo-root ``animus.env`` → ``animus-chat/animus.env`` →
    ``animus-chat/hermes-chat.env`` → ``<CHAT_DATA_DIR>/config.json`` (``hermes_dashboard_session_token``).

    The config file path is used when the token is saved from Settings (or hand-edited) but systemd
    does not inject ``HERMES_DASHBOARD_SESSION_TOKEN`` into the chat process.
    """
    t = (os.environ.get("HERMES_DASHBOARD_SESSION_TOKEN") or "").strip()
    if t:
        return t
    for p in (_REPO_ROOT / "animus.env", _CHAT_PKG / "animus.env", _CHAT_PKG / "hermes-chat.env"):
        t = _parse_env_file_for_key(p, "HERMES_DASHBOARD_SESSION_TOKEN")
        if t:
            return t
    return _dashboard_token_from_chat_config()


def _dashboard_headers() -> dict[str, str]:
    tok = hermes_dashboard_session_token()
    h: dict[str, str] = {"Accept": "application/json"}
    if tok:
        h["X-Hermes-Session-Token"] = tok
    return h


async def gateway_http_json(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    timeout: float = 60.0,
) -> tuple[int, Any]:
    """HTTP JSON to ``HERMES_API_URL`` (gateway). Path must start with ``/``."""
    url = hermes_api_base() + path
    headers = dict(gateway_upstream_headers())
    headers.setdefault("Accept", "application/json")
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as c:
            r = await c.request(method.upper(), url, headers=headers, json=json_body)
    except Exception as exc:
        log.warning("gateway %s %s failed: %s", method, path, exc)
        return 0, {"error": str(exc)}
    try:
        body = r.json() if r.content else {}
    except json.JSONDecodeError:
        body = {"error": (r.text or "")[:2000] or f"HTTP {r.status_code}", "raw": True}
    return r.status_code, body


async def dashboard_http_json(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    timeout: float = 60.0,
) -> tuple[int, Any]:
    """HTTP JSON to Hermes dashboard (requires ``HERMES_DASHBOARD_SESSION_TOKEN`` for gated routes)."""
    url = hermes_dashboard_base() + path
    headers = _dashboard_headers()
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as c:
            r = await c.request(method.upper(), url, headers=headers, json=json_body)
    except Exception as exc:
        log.warning("dashboard %s %s failed: %s", method, path, exc)
        return 0, {"detail": str(exc)}
    try:
        body = r.json() if r.content else {}
    except json.JSONDecodeError:
        body = {"detail": (r.text or "")[:2000] or f"HTTP {r.status_code}"}
    return r.status_code, body


async def dashboard_post_gateway_restart(*, timeout: float = 12.0) -> tuple[int, dict[str, Any]]:
    """Short default timeout so ANIMUS ``POST /api/restart/gateway`` does not hang behind a dead dashboard."""
    return await dashboard_http_json("POST", "/api/gateway/restart", json_body={}, timeout=timeout)


async def dashboard_get_skills() -> tuple[int, Any]:
    return await dashboard_http_json("GET", "/api/skills")


async def dashboard_put_skill_toggle(name: str, enabled: bool) -> tuple[int, Any]:
    return await dashboard_http_json("PUT", "/api/skills/toggle", json_body={"name": name, "enabled": enabled})


async def dashboard_get_analytics_usage(days: int = 30) -> tuple[int, Any]:
    return await dashboard_http_json("GET", f"/api/analytics/usage?days={max(1, min(int(days), 366))}")


async def dashboard_get_config() -> tuple[int, Any]:
    return await dashboard_http_json("GET", "/api/config")


async def dashboard_put_config(config: dict[str, Any]) -> tuple[int, Any]:
    return await dashboard_http_json("PUT", "/api/config", json_body={"config": config})


async def dashboard_kanban_get(subpath: str, *, query: str = "", timeout: float = 60.0) -> tuple[int, Any]:
    """GET ``/api/plugins/kanban/{subpath}`` (requires dashboard session token)."""
    path = f"/api/plugins/kanban/{subpath.lstrip('/')}"
    if query:
        path = f"{path}?{query}"
    return await dashboard_http_json("GET", path, timeout=timeout)


def _dashboard_ws_base_url() -> str:
    """``ws://`` or ``wss://`` base for WebSocket upgrade (no path)."""
    base = hermes_dashboard_base().strip().rstrip("/")
    parts = urlsplit(base)
    scheme = "wss" if parts.scheme == "https" else "ws"
    return urlunsplit((scheme, parts.netloc, "", "", ""))


async def dashboard_ws_json_rpc_call(
    method: str,
    params: dict[str, Any],
    *,
    timeout: float = 60.0,
) -> tuple[int, dict[str, Any]]:
    """Single JSON-RPC request over Hermes dashboard ``/api/ws`` (from ANIMUS host → loopback).

    Handles both inline ``dispatch`` responses and pool-scheduled handlers that
    respond asynchronously on the same WebSocket.

    Returns ``(status, payload)`` where ``payload`` includes ``result`` or ``error``
    mirroring JSON-RPC, plus ``_rpc_ok`` when status is 200.
    """
    if websockets is None:
        return 503, {"detail": "websockets package not installed", "_rpc_ok": False}
    tok = hermes_dashboard_session_token()
    if not tok:
        return 401, {"detail": "HERMES_DASHBOARD_SESSION_TOKEN not set", "_rpc_ok": False}
    ws_base = _dashboard_ws_base_url()
    uri = f"{ws_base}/api/ws?token={quote(tok, safe='')}"
    rid = random.randint(1, 2_147_483_647)
    line_out = json.dumps(
        {"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}},
        ensure_ascii=False,
    )

    # Server sends ``gateway.ready`` immediately; drain it (or stray frames) then send RPC.
    try:
        async with websockets.connect(
            uri,
            open_timeout=min(15.0, timeout),
            close_timeout=2.0,
            max_size=16_777_216,
        ) as ws:
            # Drain gateway.ready (and any startup events) then send.
            deadline = asyncio.get_event_loop().time() + min(5.0, timeout)
            while asyncio.get_event_loop().time() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    break
                if not isinstance(raw, str):
                    continue
                try:
                    msg = json.loads(raw.strip())
                except json.JSONDecodeError:
                    continue
                if msg.get("method") == "event" and (msg.get("params") or {}).get("type") == "gateway.ready":
                    break
            await ws.send(line_out)
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    return 504, {"detail": "tui-rpc timeout", "_rpc_ok": False, "method": method}
                if not isinstance(raw, str):
                    continue
                raw_st = raw.strip()
                if not raw_st:
                    continue
                try:
                    msg = json.loads(raw_st)
                except json.JSONDecodeError:
                    continue
                if msg.get("method") == "event":
                    continue
                if msg.get("id") == rid:
                    if "error" in msg:
                        err = msg["error"]
                        if isinstance(err, dict):
                            return 200, {"error": err, "_rpc_ok": True, "method": method}
                        return 200, {"error": {"message": str(err)}, "_rpc_ok": True, "method": method}
                    return 200, {"result": msg.get("result"), "_rpc_ok": True, "method": method}
    except Exception as exc:
        resp = getattr(exc, "response", None)
        code = getattr(resp, "status_code", None) or getattr(exc, "status_code", None) or 0
        if code == 4403:
            return 503, {
                "detail": "Hermes dashboard refused WebSocket (embedded chat disabled or non-loopback)",
                "_rpc_ok": False,
                "ws_status": code,
            }
        if code == 4401:
            return 401, {"detail": "Hermes dashboard WebSocket unauthorized", "_rpc_ok": False}
        if code:
            return 502, {"detail": f"WebSocket HTTP {code}", "_rpc_ok": False}
        log.warning("dashboard ws rpc %s failed: %s", method, exc)
        return 0, {"detail": str(exc), "_rpc_ok": False}
