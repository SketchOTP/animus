"""Hermes runtime control plane — dashboard proxy, curator, kanban (ANIMUS host-side)."""

from __future__ import annotations

import logging
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from hermes_runner import run_hermes
from hermes_service_client import (
    dashboard_http_json,
    dashboard_ws_json_rpc_call,
    hermes_dashboard_session_token,
)

log = logging.getLogger("animus.runtime")

_TUI_RPC_ALLOWED = frozenset({"commands.catalog", "complete.slash"})

# Read-only kanban dashboard paths (see plugins/kanban/dashboard/plugin_api.py).
_KANBAN_GET_ALLOWED = frozenset(
    {
        "board",
        "boards",
        "stats",
        "diagnostics",
        "config",
        "assignees",
        "home-channels",
    }
)


def _dashboard_token_required() -> JSONResponse | None:
    if hermes_dashboard_session_token():
        return None
    return JSONResponse(
        {
            "ok": False,
            "error": "HERMES_DASHBOARD_SESSION_TOKEN not set (Settings → Server or animus.env)",
        },
        status_code=401,
    )


async def hermes_runtime_tui_rpc(request: Request) -> JSONResponse:
    """Single JSON-RPC call via Hermes dashboard WebSocket (server-side loopback)."""
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"detail": "invalid JSON"}, status_code=400)
    method = (payload.get("method") or "").strip()
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    if not method:
        return JSONResponse({"detail": "method required"}, status_code=400)
    if method not in _TUI_RPC_ALLOWED:
        return JSONResponse({"detail": f"method not allowed: {method}"}, status_code=403)
    timeout = float(payload.get("timeout") or 60.0)
    timeout = max(5.0, min(timeout, 120.0))
    st, body = await dashboard_ws_json_rpc_call(method, params, timeout=timeout)
    http_st = st if st else 502
    if http_st == 200 and body.get("_rpc_ok"):
        return JSONResponse(body, status_code=200)
    return JSONResponse(body, status_code=http_st if http_st != 200 else 200)


async def hermes_curator_status(_request: Request) -> JSONResponse:
    """GET /api/hermes/curator/status — enabled/paused/last run (reads ~/.hermes curator state)."""
    try:
        from agent import curator
        state = curator.load_state()
        enabled = curator.is_enabled()
        paused = bool(state.get("paused"))
        return JSONResponse(
            {
                "ok": True,
                "enabled": enabled,
                "paused": paused,
                "status": (
                    "enabled"
                    if enabled and not paused
                    else "paused"
                    if paused
                    else "disabled"
                ),
                "run_count": state.get("run_count", 0),
                "last_run_at": state.get("last_run_at"),
                "last_run_summary": state.get("last_run_summary"),
            }
        )
    except Exception as exc:
        log.warning("curator status failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


async def hermes_curator_run(_request: Request) -> JSONResponse:
    """POST /api/hermes/curator/run — synchronous ``hermes curator run``."""
    res = run_hermes(["curator", "run"], timeout=600)
    return JSONResponse(
        {
            "ok": res.get("ok"),
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", ""),
            "returncode": res.get("returncode"),
        },
        status_code=200 if res.get("ok") else 502,
    )


async def hermes_curator_pause(_request: Request) -> JSONResponse:
    res = run_hermes(["curator", "pause"], timeout=30)
    return JSONResponse(
        {"ok": res.get("ok"), "stdout": res.get("stdout"), "stderr": res.get("stderr")},
        status_code=200 if res.get("ok") else 502,
    )


async def hermes_curator_resume(_request: Request) -> JSONResponse:
    res = run_hermes(["curator", "resume"], timeout=30)
    return JSONResponse(
        {"ok": res.get("ok"), "stdout": res.get("stdout"), "stderr": res.get("stderr")},
        status_code=200 if res.get("ok") else 502,
    )


async def hermes_kanban_proxy(request: Request) -> JSONResponse:
    """GET /api/hermes/kanban/{path} — proxy to dashboard ``/api/plugins/kanban/`` (read-only)."""
    auth = _dashboard_token_required()
    if auth is not None:
        return auth
    sub = (request.path_params.get("path") or "").strip().strip("/")
    if not sub:
        return JSONResponse({"detail": "path required"}, status_code=400)
    head = sub.split("/", 1)[0]
    if request.method != "GET" or head not in _KANBAN_GET_ALLOWED:
        return JSONResponse(
            {"detail": f"kanban proxy: GET only, allowed roots: {sorted(_KANBAN_GET_ALLOWED)}"},
            status_code=403,
        )
    qs = request.url.query
    dash_path = f"/api/plugins/kanban/{sub}"
    if qs:
        dash_path = f"{dash_path}?{qs}"
    st, body = await dashboard_http_json("GET", dash_path, timeout=60.0)
    if st == 401:
        return JSONResponse(body if isinstance(body, dict) else {"detail": "unauthorized"}, status_code=401)
    if st == 0:
        return JSONResponse(body if isinstance(body, dict) else {"error": "dashboard unreachable"}, status_code=502)
    return JSONResponse(body if isinstance(body, dict) else {"raw": body}, status_code=st)


def runtime_route_table():
    from starlette.routing import Route

    return [
        Route("/api/hermes/runtime/tui-rpc", hermes_runtime_tui_rpc, methods=["POST"]),
        Route("/api/hermes/curator/status", hermes_curator_status, methods=["GET"]),
        Route("/api/hermes/curator/run", hermes_curator_run, methods=["POST"]),
        Route("/api/hermes/curator/pause", hermes_curator_pause, methods=["POST"]),
        Route("/api/hermes/curator/resume", hermes_curator_resume, methods=["POST"]),
        Route("/api/hermes/kanban/{path:path}", hermes_kanban_proxy, methods=["GET"]),
    ]
