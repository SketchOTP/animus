"""Call Hermes gateway (OpenAI server, port 8642) and optional Hermes dashboard (9119) from ANIMUS."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import httpx

from hermes_runner import gateway_upstream_headers

log = logging.getLogger("animus.hermes_service")


def hermes_api_base() -> str:
    return (os.environ.get("HERMES_API_URL") or "http://127.0.0.1:8642").strip().rstrip("/")


def hermes_dashboard_base() -> str:
    return (os.environ.get("HERMES_DASHBOARD_URL") or "http://127.0.0.1:9119").strip().rstrip("/")


def hermes_dashboard_session_token() -> str:
    return (os.environ.get("HERMES_DASHBOARD_SESSION_TOKEN") or "").strip()


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
