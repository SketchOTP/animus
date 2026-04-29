"""Slack webhook / bot settings (Phase 7) — reads and writes repo-root ``animus.env``."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

log = logging.getLogger("animus.slack")

_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _ROOT / "animus.env"


def _read_env_file() -> list[str]:
    if not _ENV_PATH.is_file():
        return []
    try:
        return _ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _upsert_env_lines(lines: list[str], updates: dict[str, str]) -> list[str]:
    """Replace existing KEY= lines or append new keys at end (preserve comments)."""
    keys_done = set()
    out: list[str] = []
    key_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    for line in lines:
        m = key_re.match(line.strip())
        if m:
            k = m.group(1)
            if k in updates:
                v = updates[k]
                if v:
                    out.append(f"{k}={v}")
                elif updates[k] == "":
                    out.append(f"{k}=")
                keys_done.add(k)
                continue
        out.append(line)
    for k, v in updates.items():
        if k in keys_done:
            continue
        if v:
            out.append(f"{k}={v}")
        else:
            out.append(f"{k}=")
    return out


def _write_env_lines(lines: list[str]) -> None:
    _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _slack_env_values() -> dict[str, str]:
    return {
        "webhook": (os.environ.get("SLACK_WEBHOOK_URL") or "").strip(),
        "bot": (os.environ.get("SLACK_BOT_TOKEN") or "").strip(),
        "channel": (os.environ.get("SLACK_DEFAULT_CHANNEL") or "").strip(),
    }


async def slack_status_api(_: Request) -> JSONResponse:
    v = _slack_env_values()
    return JSONResponse(
        {
            "configured": bool(v["webhook"]),
            "has_bot_token": bool(v["bot"]),
            "has_default_channel": bool(v["channel"]),
        },
    )


async def slack_save_api(req: Request) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "invalid json"}, status_code=400)
    wh = str(body.get("webhook_url") or body.get("SLACK_WEBHOOK_URL") or "").strip()
    bot = str(body.get("bot_token") or body.get("SLACK_BOT_TOKEN") or "").strip()
    ch = str(body.get("default_channel") or body.get("SLACK_DEFAULT_CHANNEL") or "").strip()
    updates: dict[str, str] = {}
    if "webhook_url" in body or "SLACK_WEBHOOK_URL" in body:
        updates["SLACK_WEBHOOK_URL"] = wh
    if "bot_token" in body or "SLACK_BOT_TOKEN" in body:
        updates["SLACK_BOT_TOKEN"] = bot
    if "default_channel" in body or "SLACK_DEFAULT_CHANNEL" in body:
        updates["SLACK_DEFAULT_CHANNEL"] = ch
    if not updates:
        return JSONResponse({"ok": False, "error": "no fields to save"}, status_code=400)
    try:
        lines = _read_env_file()
        lines = _upsert_env_lines(lines, updates)
        _write_env_lines(lines)
        for k, v in updates.items():
            os.environ[k] = v
    except OSError as exc:
        log.warning("slack_save: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    return JSONResponse({"ok": True})


async def slack_test_api(_: Request) -> JSONResponse:
    wh = _slack_env_values()["webhook"]
    if not wh:
        return JSONResponse({"ok": False, "error": "No webhook URL configured"})
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(wh, json={"text": "ANIMUS Slack integration is configured correctly."})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:500]})
    ok = 200 <= r.status_code < 300
    err = None if ok else (r.text or r.reason_phrase or "")[:800]
    return JSONResponse({"ok": ok, "error": err, "status_code": r.status_code})


def slack_route_table():
    from starlette.routing import Route

    return [
        Route("/api/integrations/slack/status", slack_status_api, methods=["GET"]),
        Route("/api/integrations/slack/save", slack_save_api, methods=["POST"]),
        Route("/api/integrations/slack/test", slack_test_api, methods=["POST"]),
    ]
