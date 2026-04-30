"""Setup wizard HTTP API (§4, §17.4 ANIMUS)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Background ``hermes auth add openai-codex`` jobs (poll_id -> metadata).
_codex_poll_jobs: dict[str, dict[str, Any]] = {}

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hermes_runner import chat_data_dir, get_hermes_bin, run_hermes

_PACKAGE_DIR = Path(__file__).resolve().parents[1]

_ENV_KEY_BY_PROVIDER: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "cohere": "COHERE_API_KEY",
    "together": "TOGETHER_API_KEY",
    "xai": "XAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def _config_path() -> Path:
    return chat_data_dir() / "config.json"


def cfg_still_first_run(cfg: dict[str, Any]) -> bool:
    """True when the first-run wizard should run (``first_run`` in ``config.json``).

    Accepts boolean false, numeric 0, and common string spellings so a hand-edited JSON
    file does not force the wizard to reappear.
    """
    v = cfg.get("first_run", True)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("0", "false", "no", "off", ""):
            return False
        if s in ("1", "true", "yes", "on"):
            return True
        return True
    if isinstance(v, (int, float)):
        return v != 0
    return True


def _load_config() -> dict[str, Any]:
    p = _config_path()
    if not p.is_file():
        return {"first_run": True}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"first_run": True}


def _save_config(cfg: dict[str, Any]) -> None:
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _model_cache_path() -> Path:
    return chat_data_dir() / "hermes_models_cache.json"


def _animus_env_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    env_path = _PACKAGE_DIR / "animus.env"
    root_env = repo_root / "animus.env"
    if not env_path.is_file() and root_env.is_file():
        env_path = root_env
    return env_path


def _read_env_kv() -> dict[str, str]:
    env_path = _animus_env_path()
    kv: dict[str, str] = {}
    if not env_path.is_file():
        return kv
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            kv[k.strip()] = v.strip()
    return kv


async def setup_status(_req: Request) -> Response:
    cfg = _load_config()
    return JSONResponse({"first_run": cfg_still_first_run(cfg)})


async def setup_hermes_check(_req: Request) -> Response:
    try:
        get_hermes_bin()
    except RuntimeError as exc:
        return JSONResponse({"ok": False, "version": None, "error": str(exc)})
    res = run_hermes(["--version"], timeout=15)
    ver = (res["stdout"] or res["stderr"] or "").strip() or "unknown"
    return JSONResponse({"ok": res["ok"], "version": ver if res["ok"] else None, "error": None if res["ok"] else res["stderr"]})


def _claude_code_authenticated() -> bool:
    """True when Claude Code CLI OAuth credentials exist and look usable."""
    ag = Path(__file__).resolve().parents[2] / "hermes-agent"
    if not ag.is_dir():
        return False
    s = str(ag)
    if s not in sys.path:
        sys.path.insert(0, s)
    try:
        from agent.anthropic_adapter import (  # type: ignore
            is_claude_code_token_valid,
            read_claude_code_credentials,
        )
    except Exception:
        return False
    try:
        creds = read_claude_code_credentials()
        if not creds:
            return False
        return bool(is_claude_code_token_valid(creds) or creds.get("refreshToken"))
    except Exception:
        return False


def _cursor_status_dict() -> dict[str, Any]:
    cursor_bin = shutil.which("cursor")
    if not cursor_bin:
        return {"status": "not_installed"}
    try:
        import subprocess

        result = subprocess.run(  # exempt: cursor whoami probe
            [cursor_bin, "whoami"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return {"status": "authenticated", "account": (result.stdout or "").strip()}
        return {"status": "not_logged_in"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


async def setup_cursor_check(_req: Request) -> Response:
    return JSONResponse(_cursor_status_dict())


async def setup_cursor_login_start(_req: Request) -> Response:
    """Best-effort: spawn ``cursor login`` (may open a browser on the host)."""
    cursor_bin = shutil.which("cursor")
    if not cursor_bin:
        return JSONResponse({"ok": False, "error": "cursor CLI not found"}, status_code=404)
    try:
        import subprocess

        subprocess.Popen(  # noqa: S603 — controlled argv; exempt: spawn cursor login for wizard
            [cursor_bin, "login"],
            start_new_session=True,
        )
        return JSONResponse({"ok": True, "message": "cursor login started on the server."})
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


async def setup_codex_auth_start(_req: Request) -> Response:
    """Spawn ``hermes auth add openai-codex`` in the background; poll ``GET …/codex-auth-status/{poll_id}``."""
    try:
        hb = get_hermes_bin()
    except RuntimeError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    poll_id = uuid.uuid4().hex
    log_dir = Path(tempfile.mkdtemp(prefix="animus-codex-auth-"))
    stdout_path = log_dir / "stdout.txt"
    stderr_path = log_dir / "stderr.txt"
    out_f = None
    err_f = None
    try:
        out_f = open(stdout_path, "wb")  # noqa: SIM115 — closed after Popen dups fds
        err_f = open(stderr_path, "wb")
        proc = subprocess.Popen(  # exempt: background hermes codex OAuth
            [hb, "auth", "add", "openai-codex"],
            stdout=out_f,
            stderr=err_f,
            start_new_session=True,
        )
    except Exception as exc:  # noqa: BLE001
        for fh in (out_f, err_f):
            if fh:
                try:
                    fh.close()
                except OSError:
                    pass
        shutil.rmtree(log_dir, ignore_errors=True)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    out_f.close()
    err_f.close()
    _codex_poll_jobs[poll_id] = {
        "proc": proc,
        "log_dir": str(log_dir),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "started": time.monotonic(),
    }
    return JSONResponse({"ok": True, "status": "pending", "poll_id": poll_id})


def _pop_codex_poll_job(poll_id: str) -> dict[str, Any] | None:
    return _codex_poll_jobs.pop(poll_id, None)


def _cleanup_codex_log_dir(log_dir: str) -> None:
    if log_dir and Path(log_dir).is_dir():
        shutil.rmtree(log_dir, ignore_errors=True)


async def setup_codex_auth_poll_status(req: Request) -> Response:
    """Poll background Codex auth: ``pending`` | ``success`` | ``failed``."""
    poll_id = str(req.path_params.get("poll_id") or "").strip()
    if not poll_id or poll_id not in _codex_poll_jobs:
        return JSONResponse({"status": "failed", "error": "unknown or expired poll_id"}, status_code=404)
    job = _codex_poll_jobs[poll_id]
    proc: subprocess.Popen = job["proc"]
    rc = proc.poll()
    if rc is None:
        return JSONResponse({"status": "pending"})
    _pop_codex_poll_job(poll_id)
    err_tail = ""
    sp = job.get("stderr_path")
    if sp:
        try:
            err_tail = Path(sp).read_text(encoding="utf-8", errors="replace")[-8000:]
        except OSError:
            pass
    _cleanup_codex_log_dir(str(job.get("log_dir") or ""))
    if rc == 0:
        return JSONResponse({"status": "success"})
    msg = (err_tail or f"process exited with code {rc}").strip()
    return JSONResponse({"status": "failed", "error": msg[:2000]})


def _codex_authenticated() -> tuple[bool, str]:
    res = run_hermes(["auth", "status", "openai-codex"], timeout=20)
    so = (res.get("stdout") or "").lower()
    authed = bool(res.get("ok")) and "logged in" in so
    detail = (res.get("stdout") or res.get("stderr") or "")[:800]
    return authed, detail


async def setup_codex_auth_session(_req: Request) -> Response:
    """Whether OpenAI Codex is already authenticated (``hermes auth status openai-codex``)."""
    authed, detail = _codex_authenticated()
    return JSONResponse({"ok": True, "authenticated": authed, "detail": detail})


async def setup_test_key(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        body = {}
    provider = str(body.get("provider") or "").strip().lower()
    key = str(body.get("key") or "").strip()
    cfg = _load_config()
    stmap = cfg.get("provider_key_status")
    if not isinstance(stmap, dict):
        stmap = {}

    if not key:
        return JSONResponse({"ok": False, "error": "key is required"})
    ok = False
    err = ""
    try:
        if provider in ("openai", ""):
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                )
            ok = r.status_code == 200
            if not ok:
                err = f"HTTP {r.status_code}"
        elif provider == "anthropic":
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-3-haiku-20240307", "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]},
                )
            ok = r.status_code in (200, 400)
            if not ok:
                err = r.text[:500]
        else:
            ok = True
            err = ""
    except Exception as exc:  # noqa: BLE001
        ok = False
        err = str(exc)

    stmap[provider] = "ready" if ok else "error"
    cfg["provider_key_status"] = stmap
    _save_config(cfg)
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": err or "test failed"})


async def setup_models(_req: Request) -> Response:
    p = _model_cache_path()
    if not p.is_file():
        return JSONResponse([])
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return JSONResponse(data)
        if isinstance(data, dict) and "models" in data:
            return JSONResponse(data["models"])
        return JSONResponse([])
    except Exception:
        return JSONResponse([])


async def setup_tailscale_check(req: Request) -> Response:
    hostname = (req.query_params.get("hostname") or "").strip()
    if not hostname:
        return JSONResponse({"ok": False, "error": "hostname is required"})
    try:

        def _resolve() -> None:
            socket.getaddrinfo(hostname, None)

        await asyncio.wait_for(asyncio.to_thread(_resolve), timeout=5.0)
        return JSONResponse({"ok": True, "url": f"https://{hostname}"})
    except asyncio.TimeoutError:
        return JSONResponse(
            {"ok": False, "error": "DNS lookup timed out. Check Tailscale is running: tailscale status"},
        )
    except OSError as e:
        return JSONResponse(
            {
                "ok": False,
                "error": str(e),
                "hint": "Check that Tailscale is running: `tailscale status`",
            },
        )


async def setup_check_path(req: Request) -> Response:
    raw = (req.query_params.get("path") or "").strip()
    if not raw:
        return JSONResponse({"ok": False, "error": "path is required"})
    expanded = Path(raw).expanduser().resolve()
    if expanded.exists() and expanded.is_dir():
        return JSONResponse({"ok": True, "resolved": str(expanded)})
    return JSONResponse({"ok": False, "error": f"Path not found or not a directory: {expanded}"})


async def setup_provider_status(_req: Request) -> Response:
    """Matrix row data: env keys, last test status, OAuth CLI probes."""
    kv = _read_env_kv()
    cfg = _load_config()
    stmap = cfg.get("provider_key_status")
    if not isinstance(stmap, dict):
        stmap = {}

    rows: list[dict[str, Any]] = []
    for prov, envk in _ENV_KEY_BY_PROVIDER.items():
        has = bool((kv.get(envk) or "").strip())
        last = str(stmap.get(prov) or "")
        if has and last == "ready":
            status = "ready"
        elif has and last == "error":
            status = "error"
        elif has:
            status = "ready"
        else:
            status = "no_key"
        rows.append({"id": prov, "kind": "api_key", "env_key": envk, "status": status, "has_key": has})

    codex_ok, _detail = _codex_authenticated()
    rows.append(
        {
            "id": "openai-codex",
            "kind": "oauth",
            "status": "ready" if codex_ok else "not_signed_in",
            "label": "OpenAI Codex",
        },
    )

    cur_j = _cursor_status_dict()
    cs = str(cur_j.get("status") or "")
    if cs == "authenticated":
        cst = "ready"
    elif cs == "not_installed":
        cst = "no_key"
    else:
        cst = "not_signed_in"
    rows.append(
        {
            "id": "cursor-agent",
            "kind": "cursor",
            "status": cst,
            "account": cur_j.get("account"),
            "label": "Cursor CLI",
        },
    )
    cc_ok = _claude_code_authenticated()
    rows.append(
        {
            "id": "claude-code",
            "kind": "oauth",
            "status": "ready" if cc_ok else "not_signed_in",
            "label": "Claude Code",
        },
    )
    rows.append(
        {
            "id": "copilot-acp",
            "kind": "hint",
            "status": "ready",
            "label": "GitHub Copilot (ACP)",
        },
    )

    return JSONResponse({"ok": True, "providers": rows})


async def setup_save_config(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        body = {}
    cfg = _load_config()
    if "default_model" in body:
        cfg["default_model"] = body.get("default_model")
    if "wake_lock" in body:
        cfg["wake_lock"] = bool(body.get("wake_lock"))
    if "tailscale_setup_ack" in body:
        cfg["tailscale_setup_ack"] = bool(body.get("tailscale_setup_ack"))
    if "tailscale_enabled" in body:
        cfg["tailscale_enabled"] = bool(body.get("tailscale_enabled"))
    if "tailscale_hostname" in body:
        cfg["tailscale_hostname"] = str(body.get("tailscale_hostname") or "").strip()
    if "tailscale_port" in body:
        try:
            cfg["tailscale_port"] = int(body.get("tailscale_port") or 3001)
        except (TypeError, ValueError):
            cfg["tailscale_port"] = 3001
    if "projects_dir" in body:
        raw = str(body.get("projects_dir") or "").strip()
        cfg["projects_dir"] = str(Path(raw).expanduser().resolve()) if raw else ""
    if "wizard_selected_providers" in body:
        v = body.get("wizard_selected_providers")
        cfg["wizard_selected_providers"] = v if isinstance(v, list) else []
    if "wizard_ready_providers" in body:
        v = body.get("wizard_ready_providers")
        cfg["wizard_ready_providers"] = v if isinstance(v, list) else []
    if "inference_models" in body and isinstance(body.get("inference_models"), dict):
        cur = cfg.get("inference_models")
        if not isinstance(cur, dict):
            cur = {}
        for k, val in body["inference_models"].items():
            cur[str(k)] = str(val)
        cfg["inference_models"] = cur

    keys = body.get("keys") if isinstance(body.get("keys"), dict) else {}
    env_path = _animus_env_path()
    lines = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    kv: dict[str, str] = {}
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            kv[k.strip()] = v.strip()
    keymap = {p: _ENV_KEY_BY_PROVIDER[p] for p in _ENV_KEY_BY_PROVIDER}
    for prov, val in keys.items():
        envk = keymap.get(str(prov).lower())
        if envk and str(val).strip():
            kv[envk] = str(val).strip()
    out = [f"{k}={v}" for k, v in sorted(kv.items())]
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.environ.update({k: v for k, v in kv.items()})
    _save_config(cfg)
    return JSONResponse({"ok": True})


async def setup_complete(_req: Request) -> Response:
    cfg = _load_config()
    cfg["first_run"] = False
    cfg["setup_completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_config(cfg)
    return JSONResponse({"ok": True})


def wizard_route_table():
    from starlette.routing import Route

    return [
        Route("/api/setup/status", setup_status, methods=["GET"]),
        Route("/api/setup/hermes-check", setup_hermes_check, methods=["GET"]),
        Route("/api/setup/cursor-check", setup_cursor_check, methods=["GET"]),
        Route("/api/setup/cursor-login-start", setup_cursor_login_start, methods=["POST"]),
        Route("/api/setup/codex-auth-start", setup_codex_auth_start, methods=["POST"]),
        Route("/api/setup/codex-auth-status/{poll_id}", setup_codex_auth_poll_status, methods=["GET"]),
        Route("/api/setup/codex-auth-session", setup_codex_auth_session, methods=["GET"]),
        Route("/api/setup/test-key", setup_test_key, methods=["POST"]),
        Route("/api/setup/models", setup_models, methods=["GET"]),
        Route("/api/setup/save-config", setup_save_config, methods=["POST"]),
        Route("/api/setup/complete", setup_complete, methods=["POST"]),
        Route("/api/setup/tailscale-check", setup_tailscale_check, methods=["GET"]),
        Route("/api/setup/check-path", setup_check_path, methods=["GET"]),
        Route("/api/setup/provider-status", setup_provider_status, methods=["GET"]),
    ]
