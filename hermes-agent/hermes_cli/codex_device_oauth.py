"""OpenAI Codex device OAuth — shared by Hermes dashboard and ANIMUS setup API.

Extracted from ``hermes_cli.web_server`` so hosts without FastAPI/uvicorn (e.g. ANIMUS
chat venv) can run the same device-code flow the dashboard uses, without importing
the full web UI module.
"""

from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from typing import Any, Dict

_log = logging.getLogger(__name__)

_OAUTH_SESSION_TTL_SECONDS = 15 * 60
_sessions: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def gc_expired_sessions() -> None:
    cutoff = time.time() - _OAUTH_SESSION_TTL_SECONDS
    with _lock:
        stale = [sid for sid, sess in _sessions.items() if sess.get("created_at", 0) < cutoff]
        for sid in stale:
            _sessions.pop(sid, None)


def _new_session() -> tuple[str, Dict[str, Any]]:
    sid = secrets.token_urlsafe(16)
    sess: Dict[str, Any] = {
        "session_id": sid,
        "provider": "openai-codex",
        "flow": "device_code",
        "created_at": time.time(),
        "status": "pending",
        "error_message": None,
    }
    with _lock:
        _sessions[sid] = sess
    return sid, sess


def cancel_session(session_id: str) -> bool:
    """Remove a pending Codex OAuth session. Returns True if one was removed."""
    with _lock:
        sess = _sessions.pop(session_id, None)
    return bool(sess)


def poll_openai_codex_oauth(session_id: str) -> Dict[str, Any]:
    with _lock:
        sess = _sessions.get(session_id)
    if not sess:
        raise KeyError(session_id)
    return {
        "session_id": session_id,
        "status": sess["status"],
        "error_message": sess.get("error_message"),
        "expires_at": sess.get("expires_at"),
    }


def _codex_worker(session_id: str) -> None:
    """Background: OpenAI Codex device-auth (same steps as dashboard worker)."""
    try:
        import httpx
        from hermes_cli.auth import (
            CODEX_OAUTH_CLIENT_ID,
            CODEX_OAUTH_TOKEN_URL,
            DEFAULT_CODEX_BASE_URL,
        )

        issuer = "https://auth.openai.com"

        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            resp = client.post(
                f"{issuer}/api/accounts/deviceauth/usercode",
                json={"client_id": CODEX_OAUTH_CLIENT_ID},
                headers={"Content-Type": "application/json"},
            )
        if resp.status_code != 200:
            raise RuntimeError(f"deviceauth/usercode returned {resp.status_code}")
        device_data = resp.json()
        user_code = device_data.get("user_code", "")
        device_auth_id = device_data.get("device_auth_id", "")
        poll_interval = max(3, int(device_data.get("interval", "5")))
        if not user_code or not device_auth_id:
            raise RuntimeError("device-code response missing user_code or device_auth_id")
        verification_url = f"{issuer}/codex/device"
        with _lock:
            sess = _sessions.get(session_id)
            if not sess:
                return
            sess["user_code"] = user_code
            sess["verification_url"] = verification_url
            sess["device_auth_id"] = device_auth_id
            sess["interval"] = poll_interval
            sess["expires_in"] = 15 * 60
            sess["expires_at"] = time.time() + sess["expires_in"]

        deadline = time.time() + float(sess["expires_in"])
        code_resp = None
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            while time.time() < deadline:
                time.sleep(poll_interval)
                poll = client.post(
                    f"{issuer}/api/accounts/deviceauth/token",
                    json={"device_auth_id": device_auth_id, "user_code": user_code},
                    headers={"Content-Type": "application/json"},
                )
                if poll.status_code == 200:
                    code_resp = poll.json()
                    break
                if poll.status_code in (403, 404):
                    continue
                raise RuntimeError(f"deviceauth/token poll returned {poll.status_code}")

        if code_resp is None:
            with _lock:
                s_exp = _sessions.get(session_id)
                if s_exp:
                    s_exp["status"] = "expired"
                    s_exp["error_message"] = "Device code expired before approval"
            return

        authorization_code = code_resp.get("authorization_code", "")
        code_verifier = code_resp.get("code_verifier", "")
        if not authorization_code or not code_verifier:
            raise RuntimeError("device-auth response missing authorization_code/code_verifier")
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            token_resp = client.post(
                CODEX_OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": f"{issuer}/deviceauth/callback",
                    "client_id": CODEX_OAUTH_CLIENT_ID,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if token_resp.status_code != 200:
            raise RuntimeError(f"token exchange returned {token_resp.status_code}")
        tokens = token_resp.json()
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        if not access_token:
            raise RuntimeError("token exchange did not return access_token")

        from agent.credential_pool import (
            AUTH_TYPE_OAUTH,
            PooledCredential,
            SOURCE_MANUAL,
            load_pool,
        )

        import uuid as _uuid

        pool = load_pool("openai-codex")
        base_url = (
            os.getenv("HERMES_CODEX_BASE_URL", "").strip().rstrip("/")
            or DEFAULT_CODEX_BASE_URL
        )
        entry = PooledCredential(
            provider="openai-codex",
            id=_uuid.uuid4().hex[:6],
            label="dashboard device_code",
            auth_type=AUTH_TYPE_OAUTH,
            priority=0,
            source=f"{SOURCE_MANUAL}:dashboard_device_code",
            access_token=access_token,
            refresh_token=refresh_token,
            base_url=base_url,
        )
        pool.add_entry(entry)
        with _lock:
            s = _sessions.get(session_id)
            if s:
                s["status"] = "approved"
        _log.info("codex device oauth completed (session=%s)", session_id)
    except Exception as e:
        _log.warning("codex device oauth worker failed (session=%s): %s", session_id, e)
        with _lock:
            s = _sessions.get(session_id)
            if s:
                s["status"] = "error"
                s["error_message"] = str(e)


async def start_openai_codex_oauth() -> Dict[str, Any]:
    """Begin Codex device OAuth; same return shape as ``web_server._start_device_code_flow``."""
    import asyncio

    gc_expired_sessions()
    sid, _ = _new_session()
    threading.Thread(
        target=_codex_worker,
        args=(sid,),
        daemon=True,
        name=f"oauth-codex-{sid[:6]}",
    ).start()
    deadline = time.time() + 10
    while time.time() < deadline:
        with _lock:
            s = _sessions.get(sid)
        if s and (s.get("user_code") or s.get("status") != "pending"):
            break
        await asyncio.sleep(0.1)
    with _lock:
        s = _sessions.get(sid, {})
    if s.get("status") == "error":
        raise RuntimeError(s.get("error_message") or "device-auth failed")
    if not s.get("user_code"):
        raise TimeoutError("device-auth timed out before returning a user code")
    return {
        "session_id": sid,
        "flow": "device_code",
        "user_code": s["user_code"],
        "verification_url": s["verification_url"],
        "expires_in": int(s.get("expires_in") or 900),
        "poll_interval": int(s.get("interval") or 5),
    }
