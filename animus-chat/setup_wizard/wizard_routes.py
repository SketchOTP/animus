"""Setup wizard HTTP API (§4, §17.4 ANIMUS)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hermes_runner import chat_data_dir, get_hermes_bin, run_hermes

log = logging.getLogger("animus.wizard")

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


def _copilot_acp_cli_resolved() -> tuple[bool, str]:
    """Best-effort: Copilot CLI on PATH (ACP sync needs the subprocess)."""
    raw_cmd = (
        (os.getenv("HERMES_COPILOT_ACP_COMMAND", "") or os.getenv("COPILOT_CLI_PATH", "") or "copilot").strip()
    )
    exe = raw_cmd.split()[0] if raw_cmd else "copilot"
    found = shutil.which(exe)
    if found:
        return True, found
    return False, exe


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


async def setup_claude_code_login_start(_req: Request) -> Response:
    """Spawn ``claude setup-token`` on the ANIMUS host (same entrypoint as Hermes / Claude Code docs)."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    "claude CLI not found on PATH. Install: npm install -g @anthropic-ai/claude-code "
                    "(restart animus.service or re-login if PATH was updated)."
                ),
            },
            status_code=404,
        )
    try:
        subprocess.Popen(  # noqa: S603 — controlled argv; exempt: spawn claude setup-token for Settings
            [claude_bin, "setup-token"],
            start_new_session=True,
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    return JSONResponse(
        {
            "ok": True,
            "message": "claude setup-token started on the server.",
            "hint": (
                "Finish the browser/terminal prompts on the ANIMUS host. "
                "If you only use SSH without a display, run `claude setup-token` in a TTY on that machine."
            ),
        },
    )


async def setup_codex_auth_start(_req: Request) -> Response:
    """Start OpenAI Codex device OAuth via Hermes ``codex_device_oauth`` (same logic as ``hermes dashboard``)."""
    try:
        from hermes_cli.codex_device_oauth import start_openai_codex_oauth

        out = await start_openai_codex_oauth()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    return JSONResponse(
        {
            "ok": True,
            "status": "pending",
            "poll_id": out.get("session_id"),
            "flow": out.get("flow"),
            "user_code": out.get("user_code"),
            "verification_url": out.get("verification_url"),
            "poll_interval": out.get("poll_interval", 3),
            "expires_in": out.get("expires_in"),
        },
    )


async def setup_codex_auth_poll_status(req: Request) -> Response:
    """Poll Codex device OAuth session (Hermes ``codex_device_oauth``): maps to ``success`` | ``failed`` | ``pending``."""
    poll_id = str(req.path_params.get("poll_id") or "").strip()
    if not poll_id:
        return JSONResponse({"status": "failed", "error": "missing poll_id"}, status_code=400)
    try:
        from hermes_cli.codex_device_oauth import poll_openai_codex_oauth

        body = poll_openai_codex_oauth(poll_id)
    except KeyError:
        return JSONResponse({"status": "failed", "error": "unknown or expired poll_id"}, status_code=404)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"status": "failed", "error": str(exc)}, status_code=500)
    raw = str(body.get("status") or "pending")
    if raw == "approved":
        return JSONResponse({"status": "success"})
    if raw in ("error", "expired", "denied"):
        return JSONResponse({"status": "failed", "error": str(body.get("error_message") or raw)[:2000]})
    return JSONResponse({"status": "pending"})


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


def _hermes_agent_src_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "hermes-agent"


def _ensure_hermes_agent_on_path() -> bool:
    ag = _hermes_agent_src_dir()
    if not ag.is_dir():
        return False
    s = str(ag)
    if s not in sys.path:
        sys.path.insert(0, s)
    return True


def _animus_provider_to_hermes(animus_id: str) -> str:
    """Map Settings inference matrix ids to Hermes ``model.provider`` slugs."""
    a = animus_id.strip().lower()
    # Hermes aliases Claude Code CLI to the Anthropic transport + Claude Code OAuth.
    return {"google": "gemini", "together": "togetherai", "claude-code": "anthropic"}.get(a, a)


def _hermes_provider_to_animus(hermes_id: str | None) -> str | None:
    if not hermes_id:
        return None
    h = str(hermes_id).strip().lower()
    return {"gemini": "google", "togetherai": "together"}.get(h, h)


def _hermes_config_model_snapshot() -> dict[str, Any]:
    """Read ``~/.hermes/config.yaml`` model.provider + model.default (raw YAML)."""
    snap: dict[str, Any] = {"hermes_active_provider": None, "hermes_default_model": None}
    if not _ensure_hermes_agent_on_path():
        return snap
    try:
        from hermes_cli.auth import _get_config_provider
        from hermes_cli.config import read_raw_config
    except Exception:
        return snap
    try:
        raw = read_raw_config() or {}
        model = raw.get("model")
        default_model: str | None = None
        provider_from_yaml: str | None = None
        if isinstance(model, str) and model.strip():
            default_model = model.strip()
        elif isinstance(model, dict):
            p = model.get("provider")
            if isinstance(p, str) and p.strip():
                provider_from_yaml = p.strip().lower()
            d = model.get("default")
            if isinstance(d, str) and d.strip():
                default_model = d.strip()
        conf_prov = _get_config_provider()
        hp = (provider_from_yaml or conf_prov or "").strip().lower() or None
        snap["hermes_active_provider"] = hp
        snap["hermes_default_model"] = default_model
        return snap
    except Exception:
        return snap


# Last-resort OpenAI-compatible (or documented) bases when models.dev / registry miss a slug.
_HERMES_SYNC_BASE_FALLBACKS: dict[str, str] = {
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "togetherai": "https://api.together.xyz/v1",
    # Cohere OpenAI-compatible API (see Cohere compatibility docs).
    "cohere": "https://api.cohere.ai/compatibility/v1",
}


def _resolve_hermes_sync_base_url(hermes_pid: str) -> str:
    """Base URL for ``_update_config_for_provider`` (Codex, registry, models.dev, env, fallbacks)."""
    if not _ensure_hermes_agent_on_path():
        return ""
    hp = (hermes_pid or "").strip().lower()
    if hp == "openai-codex":
        try:
            from hermes_cli.auth import DEFAULT_CODEX_BASE_URL

            return str(DEFAULT_CODEX_BASE_URL).rstrip("/")
        except Exception:
            return ""
    try:
        from hermes_cli.auth import PROVIDER_REGISTRY

        pc0 = PROVIDER_REGISTRY.get(hp)
        evn = getattr(pc0, "base_url_env_var", "") if pc0 else ""
        if evn:
            raw = (os.getenv(evn, "") or "").strip().rstrip("/")
            if raw:
                return raw
    except Exception:
        pass
    try:
        from hermes_cli.config import load_config
        from hermes_cli.providers import resolve_provider_full

        cfg = load_config()
        user_p = cfg.get("providers") if isinstance(cfg.get("providers"), dict) else None
        custom = cfg.get("custom_providers") if isinstance(cfg.get("custom_providers"), list) else None
        pdef = resolve_provider_full(hp, user_p, custom)
        if pdef is not None:
            bu = (getattr(pdef, "base_url", None) or "").strip()
            if bu:
                return bu.rstrip("/")
    except Exception:
        pass
    try:
        from hermes_cli.auth import PROVIDER_REGISTRY

        pc = PROVIDER_REGISTRY.get(hp)
        if pc and (getattr(pc, "inference_base_url", None) or "").strip():
            return str(pc.inference_base_url).rstrip("/")
    except Exception:
        pass
    if hp == "openai":
        raw = (os.getenv("OPENAI_BASE_URL", "") or "").strip().rstrip("/")
        return raw or "https://api.openai.com/v1"
    return (_HERMES_SYNC_BASE_FALLBACKS.get(hp) or "").strip().rstrip("/")


async def setup_sync_hermes_model(req: Request) -> Response:
    """Write Hermes ``config.yaml`` active provider + default model (CLI / gateway source of truth)."""
    try:
        body = await req.json()
    except Exception:
        body = {}
    animus_pid = str(body.get("provider") or "").strip().lower()
    model_id = str(body.get("model") or "").strip()
    if not animus_pid:
        return JSONResponse({"ok": False, "error": "provider is required"}, status_code=400)
    hermes_pid = _animus_provider_to_hermes(animus_pid)
    if animus_pid == "openai-codex":
        codex_ok, detail = _codex_authenticated()
        if not codex_ok:
            return JSONResponse(
                {"ok": False, "error": "OpenAI Codex is not signed in", "detail": (detail or "")[:800]},
                status_code=400,
            )
    elif animus_pid == "cursor-agent":
        cur = _cursor_status_dict()
        if str(cur.get("status") or "") != "authenticated":
            return JSONResponse(
                {
                    "ok": False,
                    "error": "Cursor CLI is not signed in on the server (run `cursor login` or use Settings → Sign in).",
                },
                status_code=400,
            )
    elif animus_pid == "claude-code":
        if not _claude_code_authenticated():
            return JSONResponse(
                {
                    "ok": False,
                    "error": "Claude Code is not signed in on the server (install @anthropic-ai/claude-code and run `claude` login).",
                },
                status_code=400,
            )
    elif animus_pid == "copilot-acp":
        ok_cp, cp_exe = _copilot_acp_cli_resolved()
        if not ok_cp:
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"Copilot CLI not found ({cp_exe!r}). Install GitHub Copilot CLI or set COPILOT_CLI_PATH / HERMES_COPILOT_ACP_COMMAND.",
                },
                status_code=400,
            )
    elif animus_pid in _ENV_KEY_BY_PROVIDER:
        envk = _ENV_KEY_BY_PROVIDER[animus_pid]
        if not (_read_env_kv().get(envk) or "").strip():
            return JSONResponse(
                {"ok": False, "error": f"Missing API key ({envk}) in animus.env"},
                status_code=400,
            )
    else:
        return JSONResponse({"ok": False, "error": "unknown provider"}, status_code=400)

    base = _resolve_hermes_sync_base_url(hermes_pid)
    if not base:
        return JSONResponse(
            {
                "ok": False,
                "error": (
                    f"Could not resolve inference base URL for {hermes_pid!r}. "
                    "Set the provider-specific *_BASE_URL env var in animus.env or Hermes ~/.hermes/.env, "
                    "or upgrade Hermes so models.dev lists this provider."
                ),
            },
            status_code=422,
        )
    if not _ensure_hermes_agent_on_path():
        return JSONResponse({"ok": False, "error": "hermes-agent source not found"}, status_code=500)
    try:
        from hermes_cli.auth import _save_model_choice, _update_config_for_provider
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    try:
        _update_config_for_provider(hermes_pid, base, default_model=None)
        if model_id:
            _save_model_choice(model_id)
        try:
            from hermes_service_client import (
                dashboard_get_config,
                dashboard_put_config,
                hermes_dashboard_session_token,
            )

            if model_id and hermes_dashboard_session_token():
                st, cur = await dashboard_get_config()
                if st == 200 and isinstance(cur, dict):
                    merged = dict(cur)
                    merged["model"] = model_id
                    st2, _body = await dashboard_put_config(merged)
                    if st2 != 200:
                        log.debug("dashboard PUT /api/config after model sync: HTTP %s", st2)
        except Exception as exc:
            log.debug("dashboard model mirror skipped: %s", exc)
        return JSONResponse({"ok": True, "hermes_provider": hermes_pid, "model": model_id or None})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:2000]}, status_code=500)


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

    hsnap = _hermes_config_model_snapshot()
    hp = hsnap.get("hermes_active_provider")
    hd = hsnap.get("hermes_default_model")
    animus_hp = _hermes_provider_to_animus(hp) if isinstance(hp, str) else None

    return JSONResponse(
        {
            "ok": True,
            "providers": rows,
            "hermes_active_provider": hp,
            "hermes_default_model": hd,
            "hermes_active_animus_id": animus_hp,
        },
    )


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
    if "projects_dir" in body and str(cfg.get("projects_dir") or "").strip():
        try:
            import importlib

            importlib.import_module("server").ensure_animus_general_project()
        except Exception:
            log.warning(
                "ensure_animus_general_project after wizard save-config failed",
                exc_info=True,
            )
    return JSONResponse({"ok": True})


async def setup_complete(_req: Request) -> Response:
    cfg = _load_config()
    cfg["first_run"] = False
    cfg["setup_completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_config(cfg)
    if str(cfg.get("projects_dir") or "").strip():
        try:
            import importlib

            importlib.import_module("server").ensure_animus_general_project()
        except Exception:
            log.warning(
                "ensure_animus_general_project after wizard complete failed",
                exc_info=True,
            )
    return JSONResponse({"ok": True})


def wizard_route_table():
    from starlette.routing import Route

    return [
        Route("/api/setup/status", setup_status, methods=["GET"]),
        Route("/api/setup/hermes-check", setup_hermes_check, methods=["GET"]),
        Route("/api/setup/cursor-check", setup_cursor_check, methods=["GET"]),
        Route("/api/setup/cursor-login-start", setup_cursor_login_start, methods=["POST"]),
        Route("/api/setup/claude-code-login-start", setup_claude_code_login_start, methods=["POST"]),
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
        Route("/api/setup/sync-hermes-model", setup_sync_hermes_model, methods=["POST"]),
    ]
