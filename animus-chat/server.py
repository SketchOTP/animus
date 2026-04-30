"""
ANIMUS chat server (Starlette)
- Serves the static PWA frontend from ./app/
- Proxies /api/chat       → Hermes API /v1/chat/completions (streaming SSE)
- Proxies /api/models     → Hermes API /v1/models
- /api/models              → UI model catalog (JSON array) + optional ``?gateway=1`` for raw gateway JSON
- /api/fs/validate        → check a server path exists and is a directory
- /api/fs/ls              → list directory contents for the path picker
- /api/plan/bootstrap     → POST ``{folder_name, content}`` — create ``<projects_sync_root>/<folder>/project_plan.md``
- /api/skills/*           → see ``skills_routes.py`` (list/detail/install/… + raw SKILL.md editor)
- /api/cron/*             → see ``cron_routes.py`` (list/create/edit/trigger/…)
- /api/hermes-chat-meta   → GET build/rev + **alignment probe** (``HERMES_HOME``, ``cron_jobs_path``,
  ``utils_base_url_host_matches_ok``, gateway ``/health/detailed`` compare). When TLS PEMs are set,
  use **https** for curl (``curl -k https://127.0.0.1:<port>/api/...``); plain ``http`` yields empty reply.
- /api/restart/gateway    → POST restart gateway (see ``HERMES_GATEWAY_SYSTEMD_UNIT``, ``HERMES_RESTART_GATEWAY_CMD``)
- /api/restart/chat       → POST schedule chat restart (after response; systemd unit or ``HERMES_RESTART_CHAT_CMD``)
- ``projects_sync_root`` from ``HERMES_CHAT_PROJECTS_SYNC_ROOT`` or ``~/Projects``; ``chat_data_dir``
- /api/convs              → load / save / delete conversations (server-side persistence)
- /api/projects           → load / save projects (server-side persistence)
- /api/project-sync-exclusions → GET/POST path exclusions (deleted workspace projects stay gone across restarts)
- /api/project-workspace/* → ensure / read / write project workspace markdown (history, repo_map, notes, project_goal) on registered project paths
- /api/project-ssh-test → POST JSON ``{user, host, port?, identity_file?}`` — non-interactive ``ssh`` probe from the chat host
- ``/api/ssh/hosts`` + ``/api/ssh/test`` → global SSH hosts (``ssh_routes.py``); token usage JSONL uses JSON fields ``"source"`` / ``"source_id"`` (``token_usage.py``)
- /api/stt/transcribe → POST multipart ``audio`` (or ``file``) — OpenAI Whisper or ``HERMES_CHAT_STT_LOCAL_URL`` HTTP service
- /api/attachment/text → POST multipart ``file`` — extract text from ``.docx`` (stdlib) or ``.pdf`` (``pdftotext`` from poppler-utils)
- /api/chat/attachments/text → same handler (fallback when reverse proxies allow only ``/api/chat`` prefixes or an old deploy lacked the primary path)
- Injects the API key server-side; never exposes it to the browser
- Optional HTTPS: set ``CHAT_SSL_CERTFILE`` and ``CHAT_SSL_KEYFILE`` (PEM paths)
  so the PWA is a secure context when you open **this server** over HTTPS. The bound port then speaks
  **TLS only**; local probes must use ``https://`` (``curl`` against ``http://`` gets an empty reply).
  **Tailscale Serve** (recommended): bind ``CHAT_HOST=127.0.0.1``, leave PEMs unset, run HTTP only;
  terminate TLS on the tailnet with ``tailscale serve --bg http://127.0.0.1:3000`` — see ``TAILSCALE-SERVE.md``.
  Set ``HERMES_CHAT_PUBLIC_URL`` (e.g. ``https://host.tailnet.ts.net``) so ``/api/hermes-chat-meta``
  stays aligned with what users open.

**Deploy:** Python keeps the old process in memory until restart. After an in-app zip update or any edit to
``server.py``, run ``./restart-after-code-change.sh`` from this directory (or
``systemctl --user restart animus.service`` / your chat unit), then confirm ``rev`` via ``/api/hermes-chat-meta``.
"""
import asyncio
import codecs
import io
import json
import logging
import os
import re
import shlex
import shutil
import subprocess  # exempt: used only for systemctl, ssh, pdftotext — never invoke ``hermes`` here (use hermes_runner).
import sys
import tempfile
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*_a, **_k):
        return False


_ANIMUS_MONOREPO_ROOT = Path(__file__).resolve().parent.parent
for _env_name in ("animus.env", "hermes-chat.env"):
    _env_path = Path(__file__).resolve().parent / _env_name
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)
_root_env = _ANIMUS_MONOREPO_ROOT / "animus.env"
if _root_env.is_file():
    load_dotenv(_root_env, override=False)

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

HERMES_API    = os.environ.get("HERMES_API_URL",  "http://127.0.0.1:8642")
HERMES_KEY    = os.environ.get("HERMES_API_KEY",  "")
HERMES_AGENT  = os.environ.get(
    "HERMES_AGENT_DIR",
    str(_ANIMUS_MONOREPO_ROOT / "hermes-agent"),
)
# Default bootstrap guide copied into each Hermes Chat project workspace (override with HERMES_CHAT_SETUP_REPO_MD).
_CHAT_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_SETUP_REPO_MD = _CHAT_PACKAGE_DIR / "setup_repo.md"
if _DEFAULT_SETUP_REPO_MD.is_file():
    os.environ.setdefault("HERMES_CHAT_SETUP_REPO_MD", str(_DEFAULT_SETUP_REPO_MD))
HOST          = os.environ.get("CHAT_HOST", "127.0.0.1")
PORT          = int(os.environ.get("CHAT_PORT", os.environ.get("PORT", "3001")))
SSL_CERTFILE = (os.environ.get("CHAT_SSL_CERTFILE") or "").strip()
SSL_KEYFILE = (os.environ.get("CHAT_SSL_KEYFILE") or "").strip()
# Browser / Tailscale URL (no secrets). Used only for meta + curl hints — PEM must cover this host.
PUBLIC_CHAT_URL = (os.environ.get("HERMES_CHAT_PUBLIC_URL") or "").strip().rstrip("/")

# Settings → Restart buttons: require a user/systemd unit *or* an explicit command (shlex-split, no shell).
HERMES_CHAT_SYSTEMD_UNIT = (
    (os.environ.get("HERMES_CHAT_SYSTEMD_UNIT") or "animus.service").strip() or "animus.service"
)
HERMES_GATEWAY_SYSTEMD_UNIT = (
    (os.environ.get("HERMES_GATEWAY_SYSTEMD_UNIT") or "hermes-gateway.service").strip()
    or "hermes-gateway.service"
)
HERMES_RESTART_CHAT_CMD = (os.environ.get("HERMES_RESTART_CHAT_CMD") or "").strip()
HERMES_RESTART_GATEWAY_CMD = (os.environ.get("HERMES_RESTART_GATEWAY_CMD") or "").strip()
HERMES_RESTART_CRON_CMD = (os.environ.get("HERMES_RESTART_CRON_CMD") or "").strip()


def _tls_enabled() -> bool:
    return bool(SSL_CERTFILE and SSL_KEYFILE)


def _meta_tls_browser_hint() -> str:
    """Explain who supplies the cert Chrome checks for typical *.ts.net + Serve setups."""
    if not PUBLIC_CHAT_URL or ".ts.net" not in PUBLIC_CHAT_URL:
        return ""
    if _tls_enabled():
        return (
            "Browser to Tailscale still uses Tailscale's certificate for the *.ts.net name; "
            "CHAT_SSL_* only secures the loopback hop (use `tailscale serve --bg "
            "https+insecure://127.0.0.1:<port>`). Regenerate mkcert if you also open "
            "https://<host>:<port> directly; SAN must list that hostname."
        )
    return (
        "With HTTP on loopback + Tailscale Serve, Chrome's padlock is from Tailscale, not mkcert. "
        "If you see Not secure, the device is usually off the tailnet, missing the Tailscale app/VPN, "
        "or using an in-app browser. Old localhost+5.pem omitted the full *.ts.net name; "
        "Regenerate mkcert PEMs so the SAN lists the hostname you open in the browser."
    )


class _ForwardedProtoHstsMiddleware(BaseHTTPMiddleware):
    """Tell browsers to prefer HTTPS when we are behind Serve with X-Forwarded-Proto: https."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
        if proto == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=15552000; includeSubDomains",
            )
        return response


def _meta_curl_example() -> str:
    """One-line curl for operators (TLS vs HTTP, optional public URL)."""
    if _tls_enabled():
        base = PUBLIC_CHAT_URL or f"https://127.0.0.1:{PORT}"
        extra = ""
        if not PUBLIC_CHAT_URL or "127.0.0.1" in base or "localhost" in base.lower():
            extra = "   # add -k if curl rejects the server cert (mkcert / dev CA)"
        return f"curl -fsS {base}/api/hermes-chat-meta | jq{extra}"
    return f"curl -fsS http://127.0.0.1:{PORT}/api/hermes-chat-meta | jq"


# Speech-to-text (optional). Local URL takes precedence over OpenAI Whisper.
STT_LOCAL_URL = (os.environ.get("HERMES_CHAT_STT_LOCAL_URL") or "").strip()
STT_OPENAI_KEY = (
    (os.environ.get("HERMES_CHAT_STT_OPENAI_KEY") or "").strip()
    or (os.environ.get("OPENAI_API_KEY") or "").strip()
)
STT_OPENAI_BASE = (
    (os.environ.get("HERMES_CHAT_STT_OPENAI_BASE") or "").strip()
    or (os.environ.get("OPENAI_BASE_URL") or "").strip()
    or "https://api.openai.com/v1"
).rstrip("/")
STT_MODEL = (os.environ.get("HERMES_CHAT_STT_MODEL") or "whisper-1").strip()


def stt_backend_public() -> str:
    """``local`` | ``openai`` | ``none`` — exposed in ``/api/hermes-chat-meta`` (no secrets)."""
    if STT_LOCAL_URL:
        return "local"
    if STT_OPENAI_KEY:
        return "openai"
    return "none"


from hermes_runner import chat_data_dir  # noqa: E402 — single source for wizard + chats + config.json
from setup_wizard.wizard_routes import cfg_still_first_run  # noqa: E402


DATA_DIR = chat_data_dir()

log = logging.getLogger("animus")


def projects_sync_root() -> Path:
    """Directory scanned for new ANIMUS projects (subfolders become entries).

    Order: ``HERMES_CHAT_PROJECTS_SYNC_ROOT`` env → ``projects_dir`` in ``config.json``
    (wizard / Settings) → ``~/projects`` then ``~/Projects``.
    """
    raw = (os.environ.get("HERMES_CHAT_PROJECTS_SYNC_ROOT") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    cfg_path = DATA_DIR / "config.json"
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                pd = str(cfg.get("projects_dir") or "").strip()
                if pd:
                    return Path(pd).expanduser().resolve()
        except Exception:
            pass
    low = Path.home() / "projects"
    if low.is_dir():
        return low.resolve()
    return (Path.home() / "Projects").resolve()

# Bumped when cron/API surface changes — curl GET /api/hermes-chat-meta on the host to verify deploy.
# After changing this file: restart the service (see ./restart-after-code-change.sh).
CHAT_SERVER_REV = "20260429-bundled-skills-sync"
CHAT_MODEL_CACHE_TTL = 5 * 60
CHAT_MODEL_CACHE: dict[str, dict] = {}

# Make Hermes internals importable for skills + cron
if HERMES_AGENT not in sys.path:
    sys.path.insert(0, HERMES_AGENT)


def _ensure_bundled_skills_seeded() -> None:
    """Copy bundled ``hermes-agent/skills/`` into ``HERMES_HOME/skills`` once per process.

    The Hermes CLI runs ``tools.skills_sync.sync_skills()`` on every ``hermes`` invocation;
    ANIMUS is usually started via ``server.py`` only, so new profiles stayed empty and
    ``GET /api/skills/list`` returned []. Mirroring CLI startup fixes fresh installs.
    """
    try:
        from tools.skills_sync import sync_skills

        result = sync_skills(quiet=True)
        copied = result.get("copied") or []
        updated = result.get("updated") or []
        if copied or updated:
            log.info(
                "Bundled Hermes skills synced into HERMES_HOME: %d copied, %d updated (total_bundled=%s)",
                len(copied),
                len(updated),
                result.get("total_bundled", "?"),
            )
    except Exception as exc:
        log.warning("Bundled skills sync skipped: %s", exc)


_ensure_bundled_skills_seeded()


def _collect_hermes_local_alignment() -> dict:
    """Hermes Chat process: HERMES_HOME, cron store, and agent tree sanity (sync).

    Used by ``/api/hermes-chat-meta`` and startup logging so misaligned
    ``HERMES_AGENT_DIR`` / ``HERMES_HOME`` / gateway drift surfaces immediately.
    """
    out: dict = {
        "hermes_agent_dir": HERMES_AGENT,
        "hermes_home_env": (os.environ.get("HERMES_HOME") or "").strip() or None,
        "hermes_home_resolved": None,
        "cron_jobs_path": None,
        "hermes_core_import_ok": False,
        "utils_base_url_host_matches_ok": False,
        "alignment_warnings": [],
    }
    try:
        from hermes_constants import get_hermes_home

        gh = get_hermes_home()
        out["hermes_home_resolved"] = str(gh.resolve())
        out["hermes_core_import_ok"] = True
    except Exception as exc:
        out["alignment_warnings"].append(f"hermes_constants.get_hermes_home failed: {exc}")

    if not out["hermes_home_env"]:
        out["alignment_warnings"].append(
            "HERMES_HOME is unset — cron API uses default ~/.hermes. Set HERMES_HOME in "
            "hermes-chat.env to the same value as hermes-gateway.service."
        )
    elif out["hermes_home_resolved"]:
        try:
            env_rp = Path(out["hermes_home_env"]).expanduser().resolve()
            got_rp = Path(out["hermes_home_resolved"]).resolve()
            if env_rp != got_rp:
                out["alignment_warnings"].append(
                    f"HERMES_HOME env resolves to {env_rp} but get_hermes_home() is {got_rp}"
                )
        except Exception as exc:
            out["alignment_warnings"].append(f"HERMES_HOME path compare failed: {exc}")

    try:
        import utils as _utils_mod

        fn = getattr(_utils_mod, "base_url_host_matches", None)
        out["utils_base_url_host_matches_ok"] = callable(fn)
        if not out["utils_base_url_host_matches_ok"]:
            out["alignment_warnings"].append(
                "utils.base_url_host_matches is missing — use the same HERMES_AGENT checkout "
                "and venv as the gateway (see hermes-chat systemd ExecStart)."
            )
    except Exception as exc:
        out["alignment_warnings"].append(f"import utils failed: {exc}")

    try:
        from cron.jobs import JOBS_FILE

        out["cron_jobs_path"] = str(JOBS_FILE.resolve())
    except Exception as exc:
        out["alignment_warnings"].append(f"cron.jobs import failed: {exc}")

    try:
        utils_py = Path(HERMES_AGENT).expanduser().resolve() / "utils.py"
        if not utils_py.is_file():
            out["alignment_warnings"].append(
                f"utils.py not found under HERMES_AGENT_DIR ({utils_py.parent})"
            )
    except Exception as exc:
        out["alignment_warnings"].append(f"HERMES_AGENT_DIR resolve failed: {exc}")

    return out


async def _merge_gateway_alignment_meta(out: dict) -> None:
    """Fetch gateway ``/health/detailed`` and compare ``hermes_home_resolved``."""
    url = f"{HERMES_API.rstrip('/')}/health/detailed"
    probe: dict = {"url": url, "ok": False}
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(url)
        probe["http_status"] = resp.status_code
        if resp.status_code != 200:
            out["alignment_warnings"].append(
                f"Gateway health/detailed returned HTTP {resp.status_code} (cron alignment check skipped)."
            )
            out["gateway_hermes_home_probe"] = probe
            return
        body = resp.json()
        probe["ok"] = True
        out["gateway_hermes_home"] = body.get("hermes_home")
        out["gateway_hermes_home_resolved"] = body.get("hermes_home_resolved")
        local_r = out.get("hermes_home_resolved")
        gw_r = out.get("gateway_hermes_home_resolved") or out.get("gateway_hermes_home")
        if local_r and gw_r:
            try:
                same = Path(local_r).resolve() == Path(str(gw_r)).expanduser().resolve()
            except Exception:
                same = os.path.normpath(local_r) == os.path.normpath(str(gw_r))
            out["hermes_home_matches_gateway"] = same
            if not same:
                out["alignment_warnings"].append(
                    f"HERMES_HOME mismatch: Chat resolved={local_r!r} gateway={gw_r!r}. "
                    "Point both at the same profile (e.g. ~/.hermes/profiles/<name>)."
                )
        else:
            out["hermes_home_matches_gateway"] = None
        out["gateway_hermes_home_probe"] = probe
    except Exception as exc:
        probe["error"] = str(exc)
        out["gateway_hermes_home_probe"] = probe
        out["alignment_warnings"].append(
            f"Could not reach gateway health/detailed ({url}): {exc}"
        )


# ─── Client prefs (wake lock, wizard state) — ``DATA_DIR/config.json`` ───────


def _read_animus_client_config() -> dict:
    p = DATA_DIR / "config.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_animus_client_config(cfg: dict) -> None:
    p = DATA_DIR / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


async def animus_client_config_get(_: Request) -> Response:
    cfg = _read_animus_client_config()
    wl = cfg.get("wake_lock", True)
    if isinstance(wl, str):
        wl = wl.strip().lower() not in ("0", "false", "no", "off")
    im = cfg.get("inference_models")
    if not isinstance(im, dict):
        im = {}
    wsp = cfg.get("wizard_selected_providers")
    wrp = cfg.get("wizard_ready_providers")
    ctz = str(cfg.get("cron_timezone") or "").strip()
    tb = str(cfg.get("tts_backend") or "piper").strip().lower()
    if tb not in ("browser", "piper"):
        tb = "browser"
    return JSONResponse(
        {
            "wake_lock": bool(wl),
            "first_run": cfg_still_first_run(cfg),
            "projects_dir": str(cfg.get("projects_dir") or "").strip(),
            "inference_models": im,
            "tts_backend": tb,
            "tailscale_enabled": bool(cfg.get("tailscale_enabled", False)),
            "tailscale_hostname": str(cfg.get("tailscale_hostname") or "").strip(),
            "tailscale_port": int(cfg.get("tailscale_port") or 3001),
            "wizard_selected_providers": wsp if isinstance(wsp, list) else [],
            "wizard_ready_providers": wrp if isinstance(wrp, list) else [],
            "cron_timezone": ctz,
        },
    )


async def animus_client_config_post(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        body = {}
    cfg = _read_animus_client_config()
    if "wake_lock" in body:
        cfg["wake_lock"] = bool(body.get("wake_lock"))
    if "projects_dir" in body:
        raw = str(body.get("projects_dir") or "").strip()
        cfg["projects_dir"] = str(Path(raw).expanduser().resolve()) if raw else ""
    if "inference_models" in body and isinstance(body.get("inference_models"), dict):
        cur = cfg.get("inference_models")
        if not isinstance(cur, dict):
            cur = {}
        for k, val in body["inference_models"].items():
            cur[str(k)] = str(val)
        cfg["inference_models"] = cur
    if "tailscale_enabled" in body:
        cfg["tailscale_enabled"] = bool(body.get("tailscale_enabled"))
    if "tailscale_hostname" in body:
        cfg["tailscale_hostname"] = str(body.get("tailscale_hostname") or "").strip()
    if "tailscale_port" in body:
        try:
            cfg["tailscale_port"] = int(body.get("tailscale_port") or 3001)
        except (TypeError, ValueError):
            cfg["tailscale_port"] = 3001
    if "cron_timezone" in body:
        raw_tz = str(body.get("cron_timezone") or "").strip()
        cfg["cron_timezone"] = raw_tz
    if "tts_backend" in body:
        tb = str(body.get("tts_backend") or "").strip().lower()
        cfg["tts_backend"] = tb if tb in ("browser", "piper") else "browser"
    _write_animus_client_config(cfg)
    return JSONResponse({"ok": True, "wake_lock": bool(cfg.get("wake_lock", True))})


def _desktop_launcher_open_url(req: Request) -> str:
    """URL the browser should use for persistence (Tailscale/public URL when set)."""
    if PUBLIC_CHAT_URL:
        return f"{PUBLIC_CHAT_URL}/"
    xf_host = (req.headers.get("x-forwarded-host") or "").split(",")[0].strip()
    xf_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    host = xf_host or (req.headers.get("host") or "").strip() or f"127.0.0.1:{PORT}"
    scheme = xf_proto if xf_proto in ("http", "https") else (req.url.scheme or "http")
    return f"{scheme}://{host}/"


def _desktop_launcher_xml_escape_url(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def animus_desktop_launcher_get(req: Request) -> Response:
    """Downloadable shortcut: Linux .desktop (xdg-open) or macOS .webloc (double-click in Finder)."""
    open_url = _desktop_launcher_open_url(req)
    fmt = (req.query_params.get("fmt") or "desktop").strip().lower()
    if fmt == "webloc":
        u = _desktop_launcher_xml_escape_url(open_url)
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            "<plist version=\"1.0\">\n<dict>\n"
            f"  <key>URL</key>\n  <string>{u}</string>\n"
            "</dict>\n</plist>\n"
        )
        return Response(
            body.encode("utf-8"),
            media_type="application/octet-stream",
            headers={"Content-Disposition": 'attachment; filename="ANIMUS.webloc"'},
        )
    quoted = shlex.quote(open_url)
    icon_line = "Icon=applications-internet"
    for _icon_name in ("ghostonlyicon.png", "icon-192.png"):
        _p = _CHAT_PACKAGE_DIR / "app" / _icon_name
        if _p.is_file():
            icon_line = f"Icon={_p}"
            break
    body = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=ANIMUS\n"
        "Comment=Open ANIMUS in your default browser (same origin as this install)\n"
        f"Exec=xdg-open {quoted}\n"
        f"{icon_line}\n"
        "Terminal=false\n"
        "Categories=Network;InstantMessaging;\n"
        "StartupNotify=true\n"
    )
    return Response(
        body.encode("utf-8"),
        media_type="application/x-desktop",
        headers={"Content-Disposition": 'attachment; filename="animus.desktop"'},
    )


def _animus_current_version() -> str:
    try:
        return (_ANIMUS_MONOREPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0"


def _version_tuple(v: str) -> list[int]:
    try:
        s = (v or "").strip().lstrip("v").split("+", 1)[0]
        parts = []
        for x in s.split("."):
            if not x:
                continue
            parts.append(int("".join(c for c in x if c.isdigit()) or "0"))
        return parts or [0]
    except Exception:
        return [0]


def _version_is_newer(latest: str, current: str) -> bool:
    return _version_tuple(latest) > _version_tuple(current)


def _safe_extract_release_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    """Reject zip-slip paths; then extract."""
    root = dest.resolve()
    for info in zf.infolist():
        name = (info.filename or "").replace("\\", "/").lstrip("/")
        if not name:
            continue
        if ".." in name.split("/"):
            raise ValueError(f"Unsafe path in release zip: {info.filename!r}")
        target = (root / name).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Zip path escapes install root: {info.filename!r}") from exc
    zf.extractall(root)


async def animus_check_updates(_: Request) -> Response:
    update_url = (os.environ.get("ANIMUS_UPDATE_URL") or "").strip()
    if not update_url:
        return JSONResponse(
            {
                "ok": False,
                "error": "Update checking is not configured for this install.",
            }
        )
    current = _animus_current_version()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(update_url)
            r.raise_for_status()
            manifest = r.json()
    except httpx.TimeoutException:
        return JSONResponse({"ok": False, "error": "Update server timed out. Check your connection."})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"Could not reach update server: {exc}"})

    latest = str(manifest.get("version") or "0.0.0").strip()
    is_newer = _version_is_newer(latest, current)
    return JSONResponse(
        {
            "ok": True,
            "current_version": current,
            "latest_version": latest,
            "status": "update_available" if is_newer else "up_to_date",
            "download_url": (manifest.get("download_url") or "") if is_newer else None,
            "notes": str(manifest.get("notes") or ""),
            "message": (f"ANIMUS v{latest} is available." if is_newer else "ANIMUS is up to date."),
        }
    )


async def animus_apply_update(_: Request) -> Response:
    update_url = (os.environ.get("ANIMUS_UPDATE_URL") or "").strip()
    if not update_url:
        return JSONResponse({"ok": False, "error": "ANIMUS_UPDATE_URL not set"})

    animus_root = _ANIMUS_MONOREPO_ROOT
    tmp_path: Optional[Path] = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(update_url)
            r.raise_for_status()
            manifest = r.json()

        download_url = (manifest.get("download_url") or "").strip()
        if not download_url:
            return JSONResponse({"ok": False, "error": "No download URL in update manifest"})

        fd, tmp_name = tempfile.mkstemp(suffix=".zip")
        os.close(fd)
        tmp_path = Path(tmp_name)

        async with httpx.AsyncClient(timeout=120.0) as dl_client:
            async with dl_client.stream("GET", download_url) as resp:
                resp.raise_for_status()
                with tmp_path.open("wb") as out_f:
                    async for chunk in resp.aiter_bytes(8192):
                        out_f.write(chunk)

        with zipfile.ZipFile(tmp_path) as zf:
            _safe_extract_release_zip(zf, animus_root)

        return JSONResponse(
            {"ok": True, "message": "Update applied. Restart ANIMUS to use the new version."}
        )
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)})
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


# ─── Chat proxy ───────────────────────────────────────────────────────────────

async def health(req: Request) -> Response:
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{HERMES_API}/health")
            return Response(r.content, media_type="application/json")
    except Exception as exc:
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=502)


async def hermes_chat_meta(req: Request) -> Response:
    """GET-only probe so you can confirm the correct ``server.py`` is bound (avoids 405 from StaticFiles on POST)."""
    payload = {
        "rev": CHAT_SERVER_REV,
        "server_py": str(Path(__file__).resolve()),
        "cron_edit_post": True,
        "projects_sync_root": str(projects_sync_root()),
        "chat_data_dir": str(DATA_DIR.resolve()),
        "stt_backend": stt_backend_public(),
        "tls_enabled": _tls_enabled(),
        "public_url": PUBLIC_CHAT_URL or None,
        "meta_curl_example": _meta_curl_example(),
    }
    payload.update(_collect_hermes_local_alignment())
    await _merge_gateway_alignment_meta(payload)
    # meta_schema / browser_tls_hint: curl `jq .meta_schema` — if missing, traffic is not this server.py.
    payload["meta_schema"] = 2
    payload["browser_tls_hint"] = _meta_tls_browser_hint() or ""
    return JSONResponse(payload)


def _model_cache_file() -> Path:
    return (DATA_DIR / "hermes_models_cache.json").resolve()


_UI_MODEL_PROVIDERS = (
    "openai",
    "anthropic",
    "claude-code",
    "google",
    "mistral",
    "groq",
    "xai",
    "deepseek",
    "together",
    "cohere",
    "openai-codex",
    "cursor-agent",
)


def _models_ui_rows() -> list[dict]:
    """Normalized rows for Settings / wizard: ``{provider, model_id, display_name, description}``."""
    rows: list[dict] = []
    p = _model_cache_file()
    if p.is_file():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("data"), list):
                for item in raw["data"]:
                    if not isinstance(item, dict):
                        continue
                    mid = str(item.get("id") or item.get("model_id") or "").strip()
                    if not mid:
                        continue
                    own = str(item.get("owned_by") or item.get("provider") or "openai").strip().lower()
                    rows.append(
                        {
                            "provider": own,
                            "model_id": mid,
                            "display_name": str(item.get("name") or mid),
                            "description": str(item.get("description") or "")[:500],
                        }
                    )
                if rows:
                    return rows
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict):
                        rows.append(
                            {
                                "provider": str(item.get("provider") or "openai"),
                                "model_id": str(item.get("model_id") or item.get("id") or ""),
                                "display_name": str(item.get("display_name") or item.get("model_id") or ""),
                                "description": str(item.get("description") or ""),
                            }
                        )
                if rows:
                    return rows
        except Exception:
            pass
    for prov in _UI_MODEL_PROVIDERS:
        try:
            for mid in _provider_model_catalog(prov):
                rows.append(
                    {
                        "provider": prov,
                        "model_id": mid,
                        "display_name": mid,
                        "description": "",
                    }
                )
        except Exception:
            continue
    return rows


def _claude_code_catalog_rows() -> list[dict]:
    """Claude Code CLI models: ``auto`` first, then Hermes ``anthropic`` catalog (alias in ``models.py``)."""
    if _ensure_hermes_agent_on_syspath() is None:
        return []
    try:
        from hermes_cli.models import _PROVIDER_MODELS  # type: ignore
    except Exception:
        return []
    mids = list(_PROVIDER_MODELS.get("anthropic") or [])
    rows: list[dict] = [
        {
            "provider": "claude-code",
            "model_id": "auto",
            "display_name": "Auto",
            "description": "Let Claude Code choose the best model",
        },
    ]
    for mid in mids:
        mid_s = str(mid).strip()
        if not mid_s:
            continue
        rows.append(
            {"provider": "claude-code", "model_id": mid_s, "display_name": mid_s, "description": ""},
        )
    return rows


async def models(req: Request) -> Response:
    if (req.query_params.get("gateway") or "").strip() == "1":
        if not (HERMES_KEY or "").strip():
            return JSONResponse({"error": "HERMES_API_KEY not configured", "data": []}, status_code=503)
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    f"{HERMES_API}/v1/models",
                    headers={"Authorization": f"Bearer {HERMES_KEY}"},
                )
            return Response(r.content, media_type="application/json")
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)
    if (req.query_params.get("source") or "").strip().lower() in ("local", "cache", "file"):
        p = _model_cache_file()
        if p.is_file():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                return JSONResponse(raw if isinstance(raw, (dict, list)) else {"data": []})
            except Exception as exc:
                return JSONResponse({"error": f"cache read failed: {exc}"}, status_code=500)
        return JSONResponse([], status_code=200)
    return JSONResponse(_models_ui_rows())


def _ensure_hermes_agent_on_syspath() -> Path | None:
    """Return resolved Hermes Agent root if present (prepended to ``sys.path`` once)."""
    ag = Path(HERMES_AGENT).expanduser().resolve()
    if not ag.is_dir():
        return None
    s = str(ag)
    if s not in sys.path:
        sys.path.insert(0, s)
    return ag


def _cursor_cli_authenticated() -> bool:
    cursor_bin = shutil.which("cursor")
    if not cursor_bin:
        return False
    try:
        r = subprocess.run(  # exempt: cursor whoami for model catalog gate
            [cursor_bin, "whoami"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0
    except OSError:
        return False


def _cursor_agent_catalog_rows() -> list[dict]:
    """Cursor CLI models when logged in; ``auto`` first (``list_cursor_cli_models`` order)."""
    if not _cursor_cli_authenticated():
        return []
    root = _ensure_hermes_agent_on_syspath()
    if root is None:
        return []
    try:
        from agent.cursor_agent_client import list_cursor_cli_models  # type: ignore
    except Exception:
        return []
    mids = list_cursor_cli_models() or ["auto"]
    seen: set[str] = set()
    ordered: list[str] = []
    for m in mids:
        key = str(m).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    if "auto" in ordered:
        ordered = ["auto"] + [x for x in ordered if x != "auto"]
    rows: list[dict] = []
    for mid in ordered:
        disp = "Auto" if mid == "auto" else mid
        desc = "Let Cursor choose the best available model" if mid == "auto" else ""
        # cursor-agent + auto on one logical line for release grep (see build-release.sh).
        rows.append(
            {"provider": "cursor-agent", "model_id": mid, "display_name": disp, "description": desc},
        )
    return rows


def _hermes_curated_ui_rows() -> list[dict]:
    """Static curated lists from bundled Hermes CLI (no gateway API key)."""
    if _ensure_hermes_agent_on_syspath() is None:
        return []
    try:
        from hermes_cli.models import _PROVIDER_MODELS  # type: ignore
    except Exception:
        return []
    alias = {"google": "gemini"}
    rows: list[dict] = []
    for prov in _UI_MODEL_PROVIDERS:
        if prov == "cursor-agent":
            continue
        if prov == "claude-code":
            rows.extend(_claude_code_catalog_rows())
            continue
        src = alias.get(prov, prov)
        mids = _PROVIDER_MODELS.get(src) or _PROVIDER_MODELS.get(prov)
        if not mids:
            continue
        for mid in mids:
            mid_s = str(mid).strip()
            if not mid_s:
                continue
            rows.append(
                {"provider": prov, "model_id": mid_s, "display_name": mid_s, "description": ""},
            )
    return rows


async def models_refresh(_req: Request) -> Response:
    """Rebuild ``hermes_models_cache.json`` from local Hermes curated lists + Cursor CLI (no API key)."""
    try:
        rows = _hermes_curated_ui_rows()
        rows.extend(_cursor_agent_catalog_rows())
        if not rows:
            return JSONResponse(
                {
                    "ok": False,
                    "error": "No model catalog (Hermes Agent bundle missing or incomplete).",
                },
                status_code=500,
            )
        _model_cache_file().parent.mkdir(parents=True, exist_ok=True)
        _model_cache_file().write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return JSONResponse({"ok": True, "cached": True, "count": len(rows)})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


async def api_version(_req: Request) -> Response:
    ver_path = _ANIMUS_MONOREPO_ROOT / "VERSION"
    app_ver = "0.0.0"
    if ver_path.is_file():
        app_ver = ver_path.read_text(encoding="utf-8").strip() or app_ver
    hermes_ver = "unavailable"
    try:
        from hermes_runner import run_hermes

        vr = run_hermes(["--version"], timeout=10)
        if vr["ok"]:
            hermes_ver = (vr["stdout"] or vr["stderr"] or "unknown").splitlines()[0].strip()
    except Exception:
        pass
    return JSONResponse({"app": app_ver, "hermes": hermes_ver, "python": sys.version.split()[0]})


def _provider_model_catalog(provider: str) -> list[str]:
    provider = (provider or "").strip()
    if not provider:
        return []
    now = time.time()
    cached = CHAT_MODEL_CACHE.get(provider)
    if cached and (now - cached.get("ts", 0)) < CHAT_MODEL_CACHE_TTL:
        return list(cached.get("models", []) or [])
    from hermes_cli.models import provider_model_ids

    models = provider_model_ids(provider)
    deduped: list[str] = []
    seen: set[str] = set()
    for mid in models or []:
        raw = str(mid or "").strip()
        if not raw:
            continue
        key = raw.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(raw)
    CHAT_MODEL_CACHE[provider] = {"models": deduped, "ts": now}
    return deduped


def _codex_auto_router_model(models: list[str]) -> str:
    """Pick the cheapest-looking catalog entry to run the router prompt."""
    if not models:
        return "gpt-5.4-mini"

    def score(model: str) -> tuple[int, int, str]:
        m = model.lower()
        s = 100
        if "nano" in m:
            s -= 60
        if "mini" in m:
            s -= 45
        if "small" in m:
            s -= 30
        if "haiku" in m:
            s -= 20
        if "max" in m or "pro" in m or "opus" in m:
            s += 60
        if "codex" in m:
            s -= 5
        return (s, len(m), m)

    return sorted(models, key=score)[0]


def _codex_auto_fallback_model(models: list[str]) -> str:
    if not models:
        return "gpt-5.2-codex"
    preferred = [
        "gpt-5.2-codex",
        "gpt-5.3-codex",
        "gpt-5.1-codex-max",
        "gpt-5.5",
        "gpt-5.4",
    ]
    lowered = {m.lower(): m for m in models}
    for p in preferred:
        if p in lowered:
            return lowered[p]
    for m in models:
        if "codex" in m.lower() and "mini" not in m.lower():
            return m
    return models[0]


def _latest_user_text(messages: list) -> str:
    for msg in reversed(messages or []):
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                typ = str(part.get("type") or "").lower()
                if typ in {"text", "input_text"} and part.get("text"):
                    parts.append(str(part.get("text")))
                elif typ in {"image_url", "input_image"}:
                    parts.append("[image]")
            return "\n".join(parts).strip()
    return ""


def _model_benchmark_context(model: str) -> str:
    m = model.lower()
    bits = []
    if "mini" in m or "nano" in m:
        bits.append("low cost / fast router or light edits")
    if "codex" in m:
        bits.append("coding-agent optimized")
    if "max" in m or "pro" in m:
        bits.append("higher capability and likely higher cost")
    if not bits:
        bits.append("general purpose")
    bits.append(
        "Use current benchmark knowledge if the router model has it; Hermes Chat does not fetch live benchmark pages in this low-latency path."
    )
    return "; ".join(bits)


def _extract_json_object(text: str) -> dict:
    raw = (text or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, flags=re.S)
    if not match:
        return {}
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _chat_completion_text(payload: dict) -> str:
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    msg = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, dict) and part.get("text"):
                out.append(str(part.get("text")))
        return "\n".join(out)
    return ""


async def _resolve_codex_auto_model(chat_body: dict) -> tuple[str, str]:
    models = [m for m in _provider_model_catalog("openai-codex") if str(m).strip().lower() != "auto"]
    if not models:
        return ("gpt-5.2-codex", "catalog unavailable")

    router_model = _codex_auto_router_model(models)
    fallback = _codex_auto_fallback_model(models)
    latest_user = _latest_user_text(chat_body.get("messages") or [])
    catalog_lines = "\n".join(f"- {m}: {_model_benchmark_context(m)}" for m in models)
    selector_body = {
        "model": router_model,
        "hermes_provider": "openai-codex",
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a cost-aware model router for Hermes Chat. Choose exactly one model "
                    "from the provided OpenAI Codex catalog for the user's request. Minimize cost, "
                    "but do not choose a model too weak for coding, debugging, long-context, or "
                    "multi-step tasks. If your current benchmark knowledge is incomplete, be honest "
                    "internally and rely on the catalog hints plus task complexity. Return JSON only: "
                    '{"model":"<candidate>","reason":"short reason"}'
                ),
            },
            {
                "role": "user",
                "content": (
                    "User request:\n"
                    f"{latest_user[:12000] or '(no user text found)'}\n\n"
                    "Available models and benchmark/capability hints:\n"
                    f"{catalog_lines}\n\n"
                    f"Fallback if uncertain: {fallback}"
                ),
            },
        ],
    }
    headers = {"Authorization": f"Bearer {HERMES_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10, read=45, write=15, pool=5)) as c:
            resp = await c.post(f"{HERMES_API}/v1/chat/completions", json=selector_body, headers=headers)
        if resp.status_code >= 400:
            log.warning("Codex auto router failed via %s: HTTP %s %s", router_model, resp.status_code, resp.text[:500])
            return (fallback, "router failed")
        picked = _extract_json_object(_chat_completion_text(resp.json()))
        selected = str(picked.get("model") or "").strip()
        allowed = {m.lower(): m for m in models}
        if selected.lower() in allowed:
            return (allowed[selected.lower()], str(picked.get("reason") or "auto selected").strip())
        log.warning("Codex auto router returned invalid model %r; falling back to %s", selected, fallback)
    except Exception as exc:
        log.warning("Codex auto router error via %s: %s", router_model, exc)
    return (fallback, "router unavailable")


def _sse_last_usage_and_model(sse_text: str) -> tuple[Optional[dict], Optional[str]]:
    """Parse concatenated SSE ``data:`` lines; return last ``usage`` object and last explicit ``model`` string."""
    last_usage: Optional[dict] = None
    last_model: Optional[str] = None
    for block in (sse_text or "").split("\n\n"):
        for line in block.split("\n"):
            line = line.strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                continue
            try:
                obj = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            u = obj.get("usage")
            if isinstance(u, dict):
                last_usage = u
            m = obj.get("model")
            if isinstance(m, str) and m.strip():
                last_model = m.strip()
    return last_usage, last_model


async def chat(req: Request) -> Response:
    if not (HERMES_KEY or "").strip():

        async def err_stream():
            payload = {
                "error": {
                    "message": "HERMES_API_KEY is not configured. Complete onboarding or edit animus.env.",
                    "type": "configuration_error",
                    "param": None,
                    "code": 503,
                }
            }
            yield f"data: {json.dumps(payload)}\n\n".encode()
            yield b"data: [DONE]\n\n"

        return StreamingResponse(err_stream(), media_type="text/event-stream")

    body = await req.body()
    codex_auto_resolved_model: Optional[str] = None
    parsed_body: dict = {}
    try:
        _pb = json.loads(body.decode("utf-8")) if body else {}
        parsed_body = _pb if isinstance(_pb, dict) else {}
        if (
            str(parsed_body.get("hermes_provider") or "").strip().lower() == "openai-codex"
            and str(parsed_body.get("model") or "").strip().lower() == "auto"
        ):
            selected, reason = await _resolve_codex_auto_model(parsed_body)
            parsed_body["model"] = selected
            body = json.dumps(parsed_body).encode("utf-8")
            codex_auto_resolved_model = selected
            log.info("Codex auto selected model=%s reason=%s", selected, reason)
    except Exception as exc:
        log.warning("Could not inspect chat body for Codex auto model routing: %s", exc)
    upstream_headers = {
        "Authorization": f"Bearer {HERMES_KEY}",
        "Content-Type": "application/json",
    }
    if sid := req.headers.get("X-Hermes-Session-Id"):
        upstream_headers["X-Hermes-Session-Id"] = sid

    _timeout = httpx.Timeout(connect=10, read=None, write=30, pool=5)

    async def stream():
        from token_usage import record_token_usage

        dec = codecs.getincrementaldecoder("utf-8")("replace")
        acc_chunks: list[str] = []

        def _record_usage_from_sse(full_text: str) -> None:
            usage, stream_model = _sse_last_usage_and_model(full_text)
            if not usage:
                return
            pr = str(parsed_body.get("hermes_provider") or parsed_body.get("provider") or "").strip()
            md = str(stream_model or parsed_body.get("model") or "").strip()
            conv = str(parsed_body.get("conversation_id") or parsed_body.get("conv_id") or "").strip()
            meta = parsed_body.get("metadata")
            if isinstance(meta, dict):
                conv = conv or str(meta.get("conversation_id") or "").strip()
            inp_raw = usage.get("prompt_tokens")
            out_raw = usage.get("completion_tokens")
            try:
                inp_i = int(inp_raw) if inp_raw is not None else None
            except (TypeError, ValueError):
                inp_i = None
            try:
                out_i = int(out_raw) if out_raw is not None else None
            except (TypeError, ValueError):
                out_i = None
            record_token_usage(pr or "unknown", md or "unknown", inp_i, out_i, "chat", conv)

        try:
            async with httpx.AsyncClient(timeout=_timeout) as c:
                async with c.stream(
                    "POST",
                    f"{HERMES_API}/v1/chat/completions",
                    content=body,
                    headers=upstream_headers,
                    timeout=_timeout,
                ) as resp:
                    if resp.status_code >= 400:
                        raw = (await resp.aread()).decode(errors="replace")
                        try:
                            parsed = json.loads(raw) if raw.strip() else {}
                        except json.JSONDecodeError:
                            parsed = {}
                        err = parsed.get("error") if isinstance(parsed, dict) else None
                        if isinstance(err, dict):
                            msg = err.get("message") or json.dumps(err)
                        elif isinstance(err, str):
                            msg = err
                        else:
                            msg = (raw or "").strip()[:4000] or f"HTTP {resp.status_code}"
                        # One SSE ``data:`` line so the Chat PWA can surface the failure
                        # (same content-type as success; avoids an empty assistant bubble).
                        payload = {
                            "error": {
                                "message": msg,
                                "type": "upstream_error",
                                "param": None,
                                "code": resp.status_code,
                            }
                        }
                        yield f"data: {json.dumps(payload)}\n\n".encode()
                        yield b"data: [DONE]\n\n"
                        return
                    async for chunk in resp.aiter_bytes():
                        acc_chunks.append(dec.decode(chunk))
                        yield chunk
        finally:
            tail = dec.decode(b"", final=True)
            if tail:
                acc_chunks.append(tail)
            _record_usage_from_sse("".join(acc_chunks))

    stream_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    if codex_auto_resolved_model:
        stream_headers["X-Hermes-Codex-Auto-Model"] = codex_auto_resolved_model

    return StreamingResponse(stream(), media_type="text/event-stream", headers=stream_headers)


# ─── Filesystem helpers ───────────────────────────────────────────────────────

async def fs_validate(req: Request) -> Response:
    path = req.query_params.get("path", "").strip()
    if not path:
        return JSONResponse({"valid": False, "error": "No path provided"})
    try:
        p = Path(path).expanduser().resolve()
        exists = p.exists()
        is_dir = p.is_dir() if exists else False
        return JSONResponse({
            "valid": exists and is_dir,
            "exists": exists,
            "is_dir": is_dir,
            "resolved": str(p),
            "error": None if (exists and is_dir) else
                     ("Not a directory" if (exists and not is_dir) else "Path not found"),
        })
    except Exception as exc:
        return JSONResponse({"valid": False, "error": str(exc)})


async def fs_ls(req: Request) -> Response:
    raw = req.query_params.get("path", "").strip() or str(Path.home())
    try:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            return JSONResponse({"error": "Path not found"}, status_code=404)
        if not p.is_dir():
            return JSONResponse({"error": "Not a directory"}, status_code=400)
        items = []
        for child in sorted(p.iterdir()):
            if child.name.startswith("."):
                continue
            try:
                items.append({"name": child.name, "is_dir": child.is_dir(), "path": str(child)})
            except PermissionError:
                pass
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return JSONResponse({"path": str(p),
                             "parent": str(p.parent) if p != p.parent else None,
                             "items": items[:200]})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


_PLAN_FOLDER_OK = re.compile(r"^[a-z][a-z0-9]{1,47}$")


def _sanitize_plan_folder_name(raw: str) -> str:
    """Single-segment directory name under ``projects_sync_root()`` (lowercase 'one word')."""
    s = re.sub(r"[^a-z0-9]+", "", (raw or "").lower())
    s = re.sub(r"^[0-9]+", "", s)
    if len(s) < 2:
        s = "plan"
    s = s[:48]
    if not _PLAN_FOLDER_OK.match(s):
        s = "plan"
    return s


async def plan_bootstrap(req: Request) -> Response:
    """Create ``<projects_sync_root>/<folder>/project_plan.md`` for an approved Plan tab handoff."""
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "expected object"}, status_code=400)
    folder = _sanitize_plan_folder_name(str(body.get("folder_name", "")))
    content = body.get("content")
    if not isinstance(content, str) or not content.strip():
        return JSONResponse({"error": "content required"}, status_code=400)
    if len(content) > 2 * 1024 * 1024:
        return JSONResponse({"error": "content too large"}, status_code=400)
    root = projects_sync_root().resolve()
    dest_dir = (root / folder).resolve()
    try:
        dest_dir.relative_to(root)
    except ValueError:
        return JSONResponse({"error": "invalid destination"}, status_code=400)
    if dest_dir.parent != root:
        return JSONResponse({"error": "invalid destination"}, status_code=400)
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / "project_plan.md"
        out_path.write_text(content, encoding="utf-8", newline="\n")
    except OSError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    return JSONResponse(
        {"ok": True, "path": str(out_path), "directory": str(dest_dir), "folder": folder}
    )


# ─── Speech-to-text (composer mic) ────────────────────────────────────────────


async def stt_transcribe(req: Request) -> Response:
    """POST multipart ``audio`` or ``file`` → ``{text}``. See ``stt_backend_public()``."""
    backend = stt_backend_public()
    if backend == "none":
        return JSONResponse(
            {
                "error": "stt_not_configured",
                "detail": "Set HERMES_CHAT_STT_LOCAL_URL or HERMES_CHAT_STT_OPENAI_KEY (or OPENAI_API_KEY).",
            },
            status_code=503,
        )
    try:
        form = await req.form()
    except Exception as exc:
        return JSONResponse({"error": "bad_form", "detail": str(exc)}, status_code=400)
    upload = form.get("audio") or form.get("file")
    if upload is None:
        return JSONResponse(
            {"error": "missing_audio", "detail": "Expected multipart field 'audio' or 'file'"},
            status_code=400,
        )
    try:
        body = await upload.read()
    except Exception as exc:
        return JSONResponse({"error": "read_failed", "detail": str(exc)}, status_code=400)
    max_bytes = 24 * 1024 * 1024
    if not body or len(body) > max_bytes:
        return JSONResponse(
            {"error": "audio_empty_or_too_large", "detail": f"Max {max_bytes} bytes"},
            status_code=400,
        )
    filename = getattr(upload, "filename", None) or "speech.webm"
    ctype = getattr(upload, "content_type", None) or "application/octet-stream"
    files = {"file": (filename, body, ctype)}
    try:
        if backend == "local":
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=20.0)) as client:
                r = await client.post(STT_LOCAL_URL, files=files)
            if r.status_code >= 400:
                return JSONResponse(
                    {"error": "local_stt_failed", "detail": (r.text or "")[:1200]},
                    status_code=502,
                )
            ct = (r.headers.get("content-type") or "").lower()
            if "json" in ct:
                try:
                    j = r.json()
                except Exception:
                    j = {}
                text = str(j.get("text", j.get("transcript", "")) or "").strip()
            else:
                text = (r.text or "").strip()
            return JSONResponse({"text": text})
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=25.0)) as client:
            r = await client.post(
                f"{STT_OPENAI_BASE}/audio/transcriptions",
                headers={"Authorization": f"Bearer {STT_OPENAI_KEY}"},
                data={"model": STT_MODEL},
                files=files,
            )
        if r.status_code >= 400:
            return JSONResponse(
                {"error": "openai_stt_failed", "detail": (r.text or "")[:1200]},
                status_code=502,
            )
        try:
            j = r.json()
        except Exception:
            return JSONResponse(
                {"error": "bad_openai_response", "detail": (r.text or "")[:500]},
                status_code=502,
            )
        text = str(j.get("text", "") or "").strip()
        return JSONResponse({"text": text})
    except httpx.RequestError as exc:
        log.warning("stt_transcribe upstream error: %s", exc)
        return JSONResponse({"error": "upstream_unreachable", "detail": str(exc)}, status_code=502)
    except Exception as exc:
        log.exception("stt_transcribe failed")
        return JSONResponse({"error": "stt_failed", "detail": str(exc)}, status_code=500)


# ─── Attachment text extraction (composer uploads) ───────────────────────────

_ATTACHMENT_TEXT_MAX_BYTES = 25 * 1024 * 1024
_ATTACHMENT_TEXT_OUT_MAX = 500_000
_DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def _extract_docx_plain_text(data: bytes) -> str:
    """Pull visible text from a ``.docx`` (Office Open XML) using stdlib only."""
    from xml.etree import ElementTree as ET

    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        raw = zf.read("word/document.xml")
    except KeyError as exc:
        raise ValueError(
            "This file is not a Word .docx (missing word/document.xml). "
            "It may be another ZIP format, corrupted, or not fully uploaded."
        ) from exc
    root = ET.fromstring(raw)
    chunks: list[str] = []
    for el in root.iter(f"{{{_DOCX_NS['w']}}}t"):
        if el.text:
            chunks.append(el.text)
        if el.tail:
            chunks.append(el.tail)
    return "".join(chunks)


def _extract_pdf_text_pdftotext(data: bytes) -> Optional[str]:
    """Return PDF text via ``pdftotext`` (poppler-utils), or ``None`` if unavailable."""
    if not shutil.which("pdftotext"):
        return None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name
    try:
        proc = subprocess.run(  # exempt: pdftotext system utility, not hermes CLI
            ["pdftotext", "-layout", path, "-"],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if proc.returncode != 0:
            log.warning("pdftotext failed rc=%s stderr=%s", proc.returncode, (proc.stderr or b"")[:500])
            return None
        return proc.stdout.decode("utf-8", errors="replace")
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


async def attachment_text_extract(req: Request) -> Response:
    """POST multipart ``file`` → ``{text, filename}`` for ``.docx`` or ``.pdf``."""
    try:
        form = await req.form()
    except Exception as exc:
        return JSONResponse({"error": "bad_form", "detail": str(exc)}, status_code=400)
    upload = form.get("file")
    if upload is None:
        return JSONResponse({"error": "missing_file"}, status_code=400)
    try:
        body = await upload.read()
    except Exception as exc:
        return JSONResponse({"error": "read_failed", "detail": str(exc)}, status_code=400)
    if not body:
        return JSONResponse({"error": "empty_file"}, status_code=400)
    if len(body) > _ATTACHMENT_TEXT_MAX_BYTES:
        return JSONResponse(
            {"error": "file_too_large", "detail": f"Max {_ATTACHMENT_TEXT_MAX_BYTES // (1024 * 1024)} MiB"},
            status_code=413,
        )
    filename = (getattr(upload, "filename", None) or "upload").strip()
    lower = filename.lower()
    ctype = (getattr(upload, "content_type", None) or "").lower()
    text = ""
    try:
        if (
            lower.endswith(".docx")
            or lower.endswith(".docm")
            or "wordprocessingml" in ctype
            or "macroenabled" in ctype
        ):
            text = _extract_docx_plain_text(body)
        elif lower.endswith(".doc"):
            return JSONResponse(
                {
                    "error": "legacy_doc",
                    "detail": "Legacy .doc is not supported. Save as .docx or PDF and try again.",
                },
                status_code=400,
            )
        elif lower.endswith(".pdf") or ctype == "application/pdf":
            extracted = _extract_pdf_text_pdftotext(body)
            if extracted is None:
                return JSONResponse(
                    {
                        "error": "pdf_extractor_unavailable",
                        "detail": "Install poppler-utils (pdftotext) on the Hermes Chat server to extract PDF text.",
                    },
                    status_code=422,
                )
            text = extracted
        else:
            return JSONResponse(
                {
                    "error": "unsupported_type",
                    "detail": "Only .docx / .docm and .pdf are supported on this endpoint.",
                },
                status_code=400,
            )
    except ValueError as exc:
        return JSONResponse({"error": "extract_failed", "detail": str(exc)}, status_code=400)
    except zipfile.BadZipFile:
        return JSONResponse({"error": "invalid_docx", "detail": "File is not a valid .docx zip archive."}, status_code=400)
    except Exception as exc:
        log.exception("attachment_text_extract failed")
        return JSONResponse({"error": "extract_failed", "detail": str(exc)}, status_code=500)
    if len(text) > _ATTACHMENT_TEXT_OUT_MAX:
        text = text[:_ATTACHMENT_TEXT_OUT_MAX] + "\n\n…(truncated)…"
    return JSONResponse({"text": text, "filename": filename})


# ─── SSH test (project modal — host runs `ssh`) ───────────────────────────────

_HOST_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]$|^[A-Za-z0-9]$")
_USER_SAFE = re.compile(r"^[a-zA-Z0-9._-]+$")


async def project_ssh_test(req: Request) -> Response:
    """POST JSON ``{user, host, port?, identity_file?}`` — non-interactive SSH probe."""
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON"}, status_code=400)
    user = str(body.get("user", "")).strip()
    host = str(body.get("host", "")).strip()
    port_raw = body.get("port", None)
    identity_file = str(body.get("identity_file", "")).strip()
    if not user or not host:
        return JSONResponse({"ok": False, "error": "user and host are required"}, status_code=400)
    if len(user) > 64 or len(host) > 253:
        return JSONResponse({"ok": False, "error": "user or host is too long"}, status_code=400)
    if not _USER_SAFE.match(user):
        return JSONResponse(
            {"ok": False, "error": "Invalid SSH user (use letters, digits, dot, underscore, hyphen)"},
            status_code=400,
        )
    if not _HOST_SAFE.match(host):
        return JSONResponse(
            {"ok": False, "error": "Invalid host (use hostname, alias, or dotted name)"},
            status_code=400,
        )
    port: Optional[int] = None
    if port_raw is not None and str(port_raw).strip() != "":
        try:
            port = int(port_raw)
        except (TypeError, ValueError):
            return JSONResponse({"ok": False, "error": "Invalid port"}, status_code=400)
        if port < 1 or port > 65535:
            return JSONResponse({"ok": False, "error": "Port out of range"}, status_code=400)

    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=12",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    if port is not None:
        cmd.extend(["-p", str(port)])
    if identity_file:
        key_path = Path(identity_file).expanduser()
        try:
            key_path = key_path.resolve()
        except OSError:
            return JSONResponse({"ok": False, "error": "Could not resolve identity file path"}, status_code=400)
        if not key_path.is_file():
            return JSONResponse({"ok": False, "error": "Identity file not found"}, status_code=400)
        cmd.extend(["-i", str(key_path)])
    cmd.append(f"{user}@{host}")
    cmd.append("exit")
    try:
        proc = subprocess.run(  # exempt: ssh client probe, not hermes CLI
            cmd,
            capture_output=True,
            text=True,
            timeout=28,
            check=False,
        )
    except subprocess.TimeoutExpired:  # exempt: ssh probe timeout (paired with subprocess.run ssh above)
        return JSONResponse({"ok": False, "error": "SSH timed out"})
    except FileNotFoundError:
        return JSONResponse(
            {"ok": False, "error": "The ssh program was not found on the Hermes Chat server"},
            status_code=500,
        )
    err = (proc.stderr or "").strip()
    if proc.returncode == 0:
        return JSONResponse({"ok": True, "message": "SSH connection succeeded", "stderr": err[:800]})
    detail = err[:1600] or (proc.stdout or "").strip()[:1600] or f"exit code {proc.returncode}"
    return JSONResponse({"ok": False, "error": "SSH failed", "detail": detail})


# ─── Persistence helpers ─────────────────────────────────────────────────────

def _data_file(name: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / name

def _read(name: str, default):
    f = _data_file(name)
    try:
        if f.exists():
            return json.loads(f.read_text("utf-8"))
    except Exception:
        log.exception("Failed to read %s", name)
    return default

def _write(name: str, data) -> None:
    f = _data_file(name)
    tmp = f.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False), "utf-8")
        tmp.replace(f)
    except Exception:
        log.exception("Failed to write %s", name)
        tmp.unlink(missing_ok=True)


# Paths the user removed from Hermes Chat — kept out of ``projects.json`` / GET /api/projects
# so deletes survive resync and multi-tab merge (see ``_merge_projects_onto_client``).
PROJECT_SYNC_EXCLUSIONS_STORE = "project_sync_exclusions.json"


def _normalize_exclusion_path(raw: object) -> str:
    """Match browser ``normalizeSyncPath`` (trim, strip trailing slashes)."""
    return str(raw or "").strip().rstrip("/")


def _read_exclusion_set() -> set[str]:
    raw = _read(PROJECT_SYNC_EXCLUSIONS_STORE, [])
    out: set[str] = set()
    if not isinstance(raw, list):
        return out
    for p in raw:
        n = _normalize_exclusion_path(p).lower()
        if n:
            out.add(n)
    return out


def _write_exclusion_set(paths: set[str]) -> None:
    _write(PROJECT_SYNC_EXCLUSIONS_STORE, sorted(paths))


def _project_row_exclusion_keys(project: dict) -> list[str]:
    """Lowercased normalized ``path`` / ``workspace_files_path`` keys for exclusion checks."""
    if not isinstance(project, dict):
        return []
    keys: list[str] = []
    for k in ("path", "workspace_files_path"):
        n = _normalize_exclusion_path(project.get(k) or "")
        if n:
            keys.append(n.lower())
    return keys


def _project_matches_exclusions(project: dict, exclusions: set[str]) -> bool:
    for k in _project_row_exclusion_keys(project):
        if k in exclusions:
            return True
    return False


def _filter_projects_by_exclusions(projects: list, exclusions: set[str]) -> list:
    if not exclusions:
        return [p for p in projects if isinstance(p, dict)]
    return [
        p
        for p in projects
        if isinstance(p, dict) and not _project_matches_exclusions(p, exclusions)
    ]


# ─── Conversations persistence ────────────────────────────────────────────────


def _is_cron_conversation(conv: dict) -> bool:
    """True if this row was created by bridge/gateway ``append_cron_to_hermes_chat``."""
    if (conv or {}).get("notification_channel") == "cron":
        return True
    for msg in (conv or {}).get("messages") or []:
        if isinstance(msg, dict) and msg.get("source") == "cron":
            return True
    return False


def _merge_cron_conversations_onto_client(disk: list, incoming: list) -> list:
    """Re-attach Hermes-cron rows that the client has not seen yet (avoids clobbering).

    The hermes-agent gateway appends to ``conversations.json`` (often via direct file
    write) while the browser may still hold a stale in-memory list. A ``POST /api/convs``
    with that list would otherwise overwrite the file and drop the cron run entirely.

    We preserve disk conversations whose ids are not in the incoming body when those rows
    are clearly cron-originated. For ordering, we keep the same relative order as on disk
    and **prepend** them in front of the client's rows (``insert(0, …)`` in cron).
    """
    if not disk or not isinstance(disk, list):
        return incoming if isinstance(incoming, list) else []
    if not isinstance(incoming, list):
        return disk
    have = {c.get("id") for c in incoming if c.get("id")}
    preserved = [c for c in disk if c.get("id") and c.get("id") not in have and _is_cron_conversation(c)]
    return preserved + incoming


def _normalize_sync_path(raw: object) -> str:
    """Normalize path keys to match desktop/mobile project rows reliably."""
    return str(raw or "").strip().rstrip("/")


def _project_merge_key(project: dict) -> str:
    """Stable dedupe key shared by desktop/mobile clients."""
    if not isinstance(project, dict):
        return ""
    path_key = _normalize_sync_path(project.get("path"))
    if path_key:
        return f"path:{path_key.lower()}"
    pid = str(project.get("id") or "").strip()
    if pid:
        return f"id:{pid.lower()}"
    return ""


def _merge_projects_onto_client(disk: list, incoming: list) -> list:
    """Merge server + client project lists to avoid stale-client clobbering.

    Multiple clients (desktop/mobile) can keep stale in-memory lists. If one client
    posts a full list directly, it can accidentally delete projects created from the
    other device. We merge by normalized path (primary) and id (fallback), with
    incoming values taking precedence on overlapping rows while preserving unmatched
    rows from both sides.
    """
    if not isinstance(disk, list):
        disk = []
    if not isinstance(incoming, list):
        return disk

    merged: list[dict] = []
    by_key: dict[str, int] = {}

    def upsert(project: dict) -> None:
        if not isinstance(project, dict):
            return
        key = _project_merge_key(project)
        if not key:
            return
        idx = by_key.get(key)
        if idx is None:
            by_key[key] = len(merged)
            merged.append(dict(project))
            return
        merged[idx] = {**merged[idx], **project}

    for row in disk:
        upsert(row)
    for row in incoming:
        upsert(row)
    return merged


async def convs_get(req: Request) -> Response:
    return JSONResponse(_read("conversations.json", []))


async def convs_save(req: Request) -> Response:
    data = await req.json()
    if not isinstance(data, list):
        return JSONResponse({"error": "expected array"}, status_code=400)
    disk = _read("conversations.json", [])
    data = _merge_cron_conversations_onto_client(disk, data)
    _write("conversations.json", data)
    return JSONResponse({"ok": True})


async def conv_delete(req: Request) -> Response:
    conv_id = req.path_params["conv_id"]
    convs = _read("conversations.json", [])
    convs = [c for c in convs if c.get("id") != conv_id]
    _write("conversations.json", convs)
    return JSONResponse({"ok": True})


async def convs_purge(req: Request) -> Response:
    _write("conversations.json", [])
    return JSONResponse({"ok": True})


# ─── Projects persistence ─────────────────────────────────────────────────────


async def projects_list_simple(_req: Request) -> Response:
    """Minimal project list for cron dropdowns: ``[{id, name}, …]``."""
    raw = _read("projects.json", [])
    if not isinstance(raw, list):
        raw = []
    excl = _read_exclusion_set()
    items: list[dict] = []
    for p in _filter_projects_by_exclusions(raw, excl):
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "").strip()
        nm = str(p.get("name") or "").strip() or "(unnamed)"
        if pid:
            items.append({"id": pid, "name": nm})
    items.sort(key=lambda x: (str(x.get("name") or "").lower(), str(x.get("id") or "")))
    return JSONResponse(items)


async def system_timezones(_req: Request) -> Response:
    import zoneinfo

    return JSONResponse({"timezones": sorted(zoneinfo.available_timezones())})


async def projects_get(req: Request) -> Response:
    raw = _read("projects.json", [])
    if not isinstance(raw, list):
        raw = []
    excl = _read_exclusion_set()
    return JSONResponse(_filter_projects_by_exclusions(raw, excl))


def _ensure_workspace_for_saved_projects(projects: list) -> None:
    """After ``projects.json`` changes, ensure markdown workspace + optional ``setup_repo.md`` per root."""
    from agent.project_workspace import ensure_workspace_files, workspace_files_path_raw

    excl = _read_exclusion_set()
    seen: set[Path] = set()
    for item in projects:
        if not isinstance(item, dict) or _project_matches_exclusions(item, excl):
            continue
        raw = workspace_files_path_raw(item)
        if not raw:
            raw = str(item.get("path") or "").strip()
        if not raw:
            continue
        try:
            root = Path(raw).expanduser().resolve()
        except OSError:
            continue
        if not root.is_dir() or root in seen:
            continue
        seen.add(root)
        try:
            _validate_single_repo_workspace_root(root)
        except ValueError:
            continue
        try:
            ensure_workspace_files(root)
        except Exception:
            log.warning("ensure_workspace_files failed for %s", root, exc_info=True)


async def projects_save(req: Request) -> Response:
    data = await req.json()
    if not isinstance(data, list):
        return JSONResponse({"error": "expected array"}, status_code=400)
    disk = _read("projects.json", [])
    merged = _merge_projects_onto_client(disk, data)
    excl = _read_exclusion_set()
    merged = _filter_projects_by_exclusions(merged, excl)
    _write("projects.json", merged)
    _ensure_workspace_for_saved_projects(merged)
    return JSONResponse({"ok": True, "count": len(merged)})


async def project_sync_exclusions_get(req: Request) -> Response:
    return JSONResponse(sorted(_read_exclusion_set()))


async def project_sync_exclusions_post(req: Request) -> Response:
    body = await req.json()
    if not isinstance(body, dict):
        return JSONResponse({"error": "expected object"}, status_code=400)
    add = body.get("add") or []
    remove = body.get("remove") or []
    if not isinstance(add, list) or not isinstance(remove, list):
        return JSONResponse({"error": "add/remove must be arrays"}, status_code=400)
    cur = _read_exclusion_set()
    for p in remove:
        n = _normalize_exclusion_path(p).lower()
        if n:
            cur.discard(n)
    for p in add:
        n = _normalize_exclusion_path(p).lower()
        if n:
            cur.add(n)
    _write_exclusion_set(cur)
    disk = _read("projects.json", [])
    if isinstance(disk, list):
        filtered = _filter_projects_by_exclusions(disk, cur)
        if len(filtered) != len(disk):
            _write("projects.json", filtered)
    return JSONResponse({"ok": True, "count": len(cur)})


# ─── Project workspace files (project_history, repo_map, notes, project_goal) ─


def _registered_project_roots() -> set[Path]:
    """Any ``path`` or ``workspace_files_path`` from ``projects.json`` may access workspace APIs."""
    data = _read("projects.json", [])
    if not isinstance(data, list):
        data = []
    data = _filter_projects_by_exclusions(data, _read_exclusion_set())
    roots: set[Path] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        for key in ("path", "workspace_files_path"):
            raw = str(item.get(key) or "").strip()
            if not raw:
                continue
            try:
                roots.add(Path(raw).expanduser().resolve())
            except Exception:
                continue
    return roots


def _require_registered_project_path(raw: str) -> Path:
    try:
        pr = Path(str(raw or "").strip()).expanduser().resolve()
    except Exception as exc:
        raise ValueError(f"Invalid path: {exc}") from exc
    if not pr.is_dir():
        raise ValueError("project path is not a directory")
    roots = _registered_project_roots()
    if pr in roots:
        return _validate_single_repo_workspace_root(pr)
    for root in roots:
        try:
            if pr.samefile(root):
                return _validate_single_repo_workspace_root(pr)
        except OSError:
            continue
    raise PermissionError("path is not a registered Hermes Chat project folder")


def _validate_single_repo_workspace_root(pr: Path) -> Path:
    """Ensure repo_map / history target one repository, not the whole Projects tree.

    - Rejects the Hermes ``projects_sync_root()`` (sibling repos would mix in).
    - Rejects strict *ancestors* of that directory (e.g. ``/home/user`` when sync
      root is ``…/Projects``), which would also walk multiple unrelated projects.
    """
    try:
        sync_root = projects_sync_root().resolve()
        pr_r = pr.resolve()
        if pr_r == sync_root:
            raise ValueError(
                "This path is the Projects directory itself, not a single project. "
                "Edit the project in Hermes Chat and set the folder to your repository "
                f"(a subdirectory under {sync_root}), then regenerate the repo map."
            )
        # If the configured Projects root lies *inside* pr, walking pr would span
        # every repo under Projects, not one project.
        try:
            sync_root.relative_to(pr_r)
        except ValueError:
            pass
        else:
            if pr_r != sync_root:
                raise ValueError(
                    "This folder is above your Hermes Projects directory. "
                    "repo_map would include unrelated repositories. "
                    "Use one repository root only (e.g. …/Projects/<repo> or an sshfs mount)."
                )
    except ValueError:
        raise
    except OSError:
        pass
    return pr


_WORKSPACE_FILE_ALIASES = {
    "project_history.md": "project_history",
    "project_goal.md": "project_goal",
    "repo_map.md": "repo_map",
    "notes.md": "notes",
    "history": "project_history",
    "goal": "project_goal",
}
_VALID_WORKSPACE_FILES = {"project_history", "repo_map", "notes", "project_goal"}


def _normalize_workspace_file_name(raw: str) -> str:
    name = str(raw or "").strip()
    if not name:
        return ""
    lowered = name.lower()
    if lowered in _WORKSPACE_FILE_ALIASES:
        return _WORKSPACE_FILE_ALIASES[lowered]
    if lowered.endswith(".md"):
        lowered = lowered[:-3]
    if lowered in _VALID_WORKSPACE_FILES:
        return lowered
    return name


async def project_workspace_ensure(req: Request) -> Response:
    try:
        body = await req.json()
        root = _require_registered_project_path(str(body.get("path", "")))
        from agent.project_workspace import ensure_workspace_files

        info = ensure_workspace_files(root)
        return JSONResponse(info)
    except PermissionError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("project_workspace_ensure failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def project_workspace_history_append(req: Request) -> Response:
    try:
        body = await req.json()
        root = _require_registered_project_path(str(body.get("path", "")))
        summary = str(body.get("summary", "") or "").strip()
        if not summary:
            return JSONResponse({"error": "summary is required"}, status_code=400)
        from agent.project_workspace import append_project_history_line

        line = append_project_history_line(root, summary, source="hermes-chat")
        return JSONResponse({"ok": True, "line": line})
    except PermissionError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("project_workspace_history_append failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def project_workspace_repo_map_refresh(req: Request) -> Response:
    try:
        body = await req.json()
        root = _require_registered_project_path(str(body.get("path", "")))
        from agent.project_workspace import refresh_repo_map

        info = refresh_repo_map(root)
        return JSONResponse({"ok": True, **info})
    except PermissionError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("project_workspace_repo_map_refresh failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def project_workspace_file_get(req: Request) -> Response:
    try:
        root = _require_registered_project_path(str(req.query_params.get("path", "")))
        raw_name = str(req.query_params.get("file", "")).strip()
        name = _normalize_workspace_file_name(raw_name)
        if name not in _VALID_WORKSPACE_FILES:
            return JSONResponse(
                {"error": "file must be project_history, repo_map, notes, or project_goal"},
                status_code=400,
            )
        from agent.project_workspace import read_workspace_file

        content = read_workspace_file(root, name, ensure=True)
        return JSONResponse({"path": str(root), "file": name, "content": content})
    except PermissionError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("project_workspace_file_get failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def project_workspace_file_put(req: Request) -> Response:
    try:
        body = await req.json()
        root = _require_registered_project_path(str(body.get("path", "")))
        raw_name = str(body.get("file", "")).strip()
        name = _normalize_workspace_file_name(raw_name)
        if name not in _VALID_WORKSPACE_FILES:
            return JSONResponse(
                {"error": "file must be project_history, repo_map, notes, or project_goal"},
                status_code=400,
            )
        content = body.get("content")
        if not isinstance(content, str):
            return JSONResponse({"error": "content (string) is required"}, status_code=400)
        from agent.project_workspace import write_workspace_file

        write_workspace_file(root, name, content)
        return JSONResponse({"ok": True, "path": str(root), "file": name})
    except PermissionError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("project_workspace_file_put failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


def _parse_restart_argv(raw: str) -> list:
    try:
        parts = shlex.split((raw or "").strip())
    except ValueError as exc:
        raise ValueError(f"Could not parse restart command: {exc}") from exc
    if not parts:
        raise ValueError("Restart command is empty")
    return parts


def _systemd_unit_missing_detail(unit: str, *, for_chat: bool) -> str:
    cmd_env = "HERMES_RESTART_CHAT_CMD" if for_chat else "HERMES_RESTART_GATEWAY_CMD"
    unit_env = "HERMES_CHAT_SYSTEMD_UNIT" if for_chat else "HERMES_GATEWAY_SYSTEMD_UNIT"
    if for_chat:
        install = (
            f"Install a user unit {unit!r} (template in this repo: systemd/hermes-chat.service → "
            f"~/.config/systemd/user/{unit}), then "
            f"`systemctl --user daemon-reload` and `systemctl --user enable --now {unit}`. "
            f"You can rename the file; set {unit_env} to match. "
        )
    else:
        install = (
            f"Install a systemd unit for the gateway named {unit!r}, or set {unit_env} to your unit "
            "file name. "
        )
    return (
        "systemctl service not found — "
        f"no unit {unit!r} visible (`systemctl --user cat …` / `sudo -n systemctl cat …`). "
        + install
        + f"If you are not using systemd, set {cmd_env} in hermes-chat.env to an executable and "
        "arguments only (parsed with shlex; no shell), for example a small script that kills "
        "and respawns the gateway or chat process."
    )


def _run_argv_now(argv: list) -> Tuple[bool, str, str]:
    cmd_str = " ".join(shlex.quote(part) for part in argv)
    try:
        res = subprocess.run(argv, capture_output=True, text=True, timeout=45, check=False)  # exempt: admin argv (restart scripts), not hermes
        if res.returncode == 0:
            return True, cmd_str, ""
        err = (res.stderr or res.stdout or "").strip()
        return False, cmd_str, err or f"command exited {res.returncode}"
    except Exception as exc:
        return False, cmd_str, str(exc)


def _service_exists(prefix: list, service: str) -> bool:
    try:
        res = subprocess.run(  # exempt: systemctl cat, not hermes CLI
            [*prefix, "cat", service],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )
        return res.returncode == 0
    except Exception:
        return False


def _pick_systemctl_prefix(service: str) -> Optional[list]:
    if _service_exists(["systemctl", "--user"], service):
        return ["systemctl", "--user"]
    if _service_exists(["sudo", "-n", "systemctl"], service):
        return ["sudo", "-n", "systemctl"]
    return None


def _restart_service_now(service: str) -> Tuple[bool, str, str]:
    prefix = _pick_systemctl_prefix(service)
    if not prefix:
        return False, "", "systemctl service not found"
    cmd = [*prefix, "restart", service]
    cmd_str = " ".join(shlex.quote(part) for part in cmd)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=12, check=False)  # exempt: systemctl restart
        if res.returncode == 0:
            return True, cmd_str, ""
        err = (res.stderr or res.stdout or "").strip()
        return False, cmd_str, err or f"systemctl exited {res.returncode}"
    except Exception as exc:
        return False, cmd_str, str(exc)


async def _delayed_systemctl_restart(service: str, delay: float) -> None:
    """Run after HTTP response is sent so mobile clients receive JSON before the process exits."""
    await asyncio.sleep(delay)
    prefix = _pick_systemctl_prefix(service)
    if not prefix:
        log.error("Background restart skipped: systemctl prefix missing for %s", service)
        return
    cmd = [*prefix, "restart", service]

    def _run_blocking() -> None:
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)  # exempt: systemctl restart background
        except Exception:
            log.exception("systemctl restart failed for %s", service)

    await asyncio.to_thread(_run_blocking)


async def _delayed_argv_restart(argv: list, delay: float) -> None:
    await asyncio.sleep(delay)

    def _run_blocking() -> None:
        try:
            subprocess.run(argv, capture_output=True, text=True, timeout=45, check=False)  # exempt: admin argv background
        except Exception:
            log.exception("Background argv restart failed: %s", argv)

    await asyncio.to_thread(_run_blocking)


async def restart_gateway(_: Request) -> Response:
    if HERMES_RESTART_GATEWAY_CMD:
        try:
            argv = _parse_restart_argv(HERMES_RESTART_GATEWAY_CMD)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
        ok, cmd_str, err = _run_argv_now(argv)
        status = 200 if ok else 500
        payload: dict = {"ok": ok, "command": cmd_str, "via": "HERMES_RESTART_GATEWAY_CMD"}
        if err:
            payload["error"] = err
        return JSONResponse(payload, status_code=status)

    unit = HERMES_GATEWAY_SYSTEMD_UNIT
    ok, cmd, err = _restart_service_now(unit)
    if not ok and err == "systemctl service not found":
        err = _systemd_unit_missing_detail(unit, for_chat=False)
    status = 200 if ok else 500
    payload = {"ok": ok, "command": cmd}
    if err:
        payload["error"] = err
    return JSONResponse(payload, status_code=status)


async def restart_chat(_: Request) -> Response:
    delay_s = 1.25
    if HERMES_RESTART_CHAT_CMD:
        try:
            argv = _parse_restart_argv(HERMES_RESTART_CHAT_CMD)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
        cmd_str = " ".join(shlex.quote(part) for part in argv)
        tasks = BackgroundTasks()
        tasks.add_task(_delayed_argv_restart, argv, delay_s)
        return JSONResponse(
            {
                "ok": True,
                "command": cmd_str,
                "scheduled": True,
                "delay_ms": int(delay_s * 1000),
                "via": "HERMES_RESTART_CHAT_CMD",
            },
            background=tasks,
        )

    unit = HERMES_CHAT_SYSTEMD_UNIT
    prefix = _pick_systemctl_prefix(unit)
    if not prefix:
        return JSONResponse(
            {
                "ok": False,
                "error": _systemd_unit_missing_detail(unit, for_chat=True),
            },
            status_code=500,
        )
    cmd = [*prefix, "restart", unit]
    cmd_str = " ".join(shlex.quote(part) for part in cmd)
    tasks = BackgroundTasks()
    tasks.add_task(_delayed_systemctl_restart, unit, delay_s)
    return JSONResponse(
        {
            "ok": True,
            "command": cmd_str,
            "scheduled": True,
            "delay_ms": int(delay_s * 1000),
        },
        background=tasks,
    )


async def restart_cron_daemon(_: Request) -> Response:
    """Best-effort cron daemon nudge / optional user-provided restart command."""
    if HERMES_RESTART_CRON_CMD:
        try:
            argv = _parse_restart_argv(HERMES_RESTART_CRON_CMD)
        except ValueError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
        ok, cmd_str, err = _run_argv_now(argv)
        return JSONResponse({"ok": ok, "error": err or None, "command": cmd_str})
    from hermes_runner import run_hermes

    tick = run_hermes(["cron", "tick", "--accept-hooks"], timeout=90)
    st = run_hermes(["cron", "status"], timeout=20)
    running = st["ok"] and ("running" in (st["stdout"] + st["stderr"]).lower())
    return JSONResponse(
        {
            "ok": tick["ok"],
            "error": (None if tick["ok"] else (tick["stderr"] or tick["stdout"] or "")[:2000]),
            "daemon_running": running,
            "via": "hermes cron tick (set HERMES_RESTART_CRON_CMD for a custom restart)",
        }
    )


# ─── App ─────────────────────────────────────────────────────────────────────

APP_DIR = Path(__file__).parent / "app"

from cron_routes import cron_route_table  # noqa: E402
from integrations_slack import slack_route_table  # noqa: E402
from setup_wizard.wizard_routes import wizard_route_table  # noqa: E402
from skills_routes import skills_route_table  # noqa: E402
from ssh_routes import ssh_route_table  # noqa: E402
from token_usage import token_usage_route_table  # noqa: E402
from tts_routes import tts_route_table  # noqa: E402
from help_routes import help_route_table  # noqa: E402


@asynccontextmanager
async def _lifespan(_app):
    """Warn when the gateway key is missing; chat requests stay blocked until configured."""
    if not (HERMES_KEY or "").strip():
        log.warning(
            "HERMES_API_KEY is unset — chat proxy is disabled until you finish the setup wizard "
            "or add the key to animus.env."
        )
    log.info(
        "ANIMUS rev=%s server_py=%s",
        CHAT_SERVER_REV,
        Path(__file__).resolve(),
    )
    local = _collect_hermes_local_alignment()
    for w in local.get("alignment_warnings") or []:
        log.warning("Hermes alignment: %s", w)
    log.info(
        "Hermes alignment: HERMES_HOME_resolved=%s cron_jobs=%s utils_ok=%s",
        local.get("hermes_home_resolved"),
        local.get("cron_jobs_path"),
        local.get("utils_base_url_host_matches_ok"),
    )
    try:
        first_warns = set(local.get("alignment_warnings") or [])
        merged = {**local, "alignment_warnings": list(local.get("alignment_warnings") or [])}
        await _merge_gateway_alignment_meta(merged)
        for w in merged.get("alignment_warnings") or []:
            if w not in first_warns:
                log.warning("Hermes alignment: %s", w)
        if merged.get("hermes_home_matches_gateway") is False:
            log.error(
                "ANIMUS HERMES_HOME does not match gateway — cron edits and execution "
                "will diverge. Fix animus.env and hermes-gateway.service, then restart both."
            )
    except Exception as exc:
        log.warning("Hermes alignment: gateway probe failed during startup: %s", exc)
    try:
        from tts_routes import schedule_default_piper_voices_if_needed

        asyncio.create_task(schedule_default_piper_voices_if_needed())
    except Exception as exc:
        log.warning("Piper voice auto-download schedule failed: %s", exc)
    yield


app = Starlette(
    lifespan=_lifespan,
    middleware=[Middleware(_ForwardedProtoHstsMiddleware)],
    routes=[
        *wizard_route_table(),
        *cron_route_table(),
        *skills_route_table(),
        *tts_route_table(),
        *token_usage_route_table(),
        *slack_route_table(),
        *ssh_route_table(),
        *help_route_table(),
        Route("/api/health",               health),
        Route("/api/hermes-chat-meta",     hermes_chat_meta, methods=["GET"]),
        Route("/api/animus-meta",          hermes_chat_meta, methods=["GET"]),
        Route("/api/version",              api_version, methods=["GET"]),
        Route("/api/animus/client-config", animus_client_config_get, methods=["GET"]),
        Route("/api/animus/client-config", animus_client_config_post, methods=["POST"]),
        Route("/api/animus/desktop-launcher", animus_desktop_launcher_get, methods=["GET"]),
        Route("/api/animus/check-updates", animus_check_updates, methods=["POST"]),
        Route("/api/animus/apply-update", animus_apply_update, methods=["POST"]),
        Route("/api/restart/gateway",      restart_gateway, methods=["POST"]),
        Route("/api/restart/chat",         restart_chat, methods=["POST"]),
        Route("/api/hermes/restart-cron",  restart_cron_daemon, methods=["POST"]),
        Route("/api/models",               models),
        Route("/api/models/refresh",       models_refresh, methods=["POST"]),
        Route("/api/chat",                 chat,         methods=["POST"]),
        Route("/api/chat/attachments/text", attachment_text_extract, methods=["POST"]),
        Route("/api/fs/validate",          fs_validate),
        Route("/api/fs/ls",                fs_ls),
        Route("/api/plan/bootstrap",       plan_bootstrap, methods=["POST"]),
        Route("/api/convs",                convs_get),
        Route("/api/convs",                convs_save,   methods=["POST"]),
        Route("/api/convs/purge",          convs_purge,  methods=["POST"]),
        Route("/api/convs/{conv_id}",      conv_delete,  methods=["DELETE"]),
        Route("/api/projects",             projects_get),
        Route("/api/projects/list-simple", projects_list_simple, methods=["GET"]),
        Route("/api/projects",             projects_save, methods=["POST"]),
        Route("/api/system/timezones",     system_timezones, methods=["GET"]),
        Route("/api/project-sync-exclusions", project_sync_exclusions_get),
        Route("/api/project-sync-exclusions", project_sync_exclusions_post, methods=["POST"]),
        Route("/api/project-workspace/ensure", project_workspace_ensure, methods=["POST"]),
        Route("/api/project-workspace/history-append", project_workspace_history_append, methods=["POST"]),
        Route("/api/project-workspace/repo-map-refresh", project_workspace_repo_map_refresh, methods=["POST"]),
        Route("/api/project-workspace/file", project_workspace_file_get, methods=["GET"]),
        Route("/api/project-workspace/file", project_workspace_file_put, methods=["PUT"]),
        Route("/api/project-ssh-test", project_ssh_test, methods=["POST"]),
        Route("/api/stt/transcribe", stt_transcribe, methods=["POST"]),
        Route("/api/attachment/text", attachment_text_extract, methods=["POST"]),
        Mount("/", StaticFiles(directory=str(APP_DIR), html=True)),
    ],
)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    use_tls = bool(SSL_CERTFILE or SSL_KEYFILE)
    if use_tls and not (SSL_CERTFILE and SSL_KEYFILE):
        log.error("HTTPS requires both CHAT_SSL_CERTFILE and CHAT_SSL_KEYFILE (PEM).")
        sys.exit(1)
    cert_path = Path(SSL_CERTFILE).expanduser() if SSL_CERTFILE else None
    key_path = Path(SSL_KEYFILE).expanduser() if SSL_KEYFILE else None
    if use_tls:
        if not cert_path.is_file():
            log.error("SSL cert file not found: %s", cert_path)
            sys.exit(1)
        if not key_path.is_file():
            log.error("SSL key file not found: %s", key_path)
            sys.exit(1)
    scheme = "https" if use_tls else "http"
    display_host = HOST
    if ":" in HOST and not HOST.startswith("["):
        display_host = f"[{HOST}]"
    log.info(
        "ANIMUS on %s://%s:%d rev=%s%s",
        scheme,
        display_host,
        PORT,
        CHAT_SERVER_REV,
        f" public_url={PUBLIC_CHAT_URL}" if PUBLIC_CHAT_URL else "",
    )
    if use_tls and PUBLIC_CHAT_URL:
        log.info("ANIMUS meta curl hint: %s", _meta_curl_example())
    if use_tls:
        log.info(
            "TLS enabled — use https for API checks, e.g. "
            "curl -k https://127.0.0.1:%d/api/hermes-chat-meta",
            PORT,
        )
    if use_tls and PUBLIC_CHAT_URL and ".ts.net" in PUBLIC_CHAT_URL.lower():
        log.warning(
            "TLS is on and HERMES_CHAT_PUBLIC_URL is *.ts.net — Tailscale Serve must use "
            "`tailscale serve --bg https+insecure://127.0.0.1:%d` (not `http://127.0.0.1:%d`). "
            "Plain HTTP to this port gives an empty curl reply.",
            PORT,
            PORT,
        )
    if HOST == "0.0.0.0":
        log.warning(
            "CHAT_HOST=0.0.0.0 — port %d is reachable on all interfaces. Use 127.0.0.1 if only "
            "Tailscale Serve (or localhost) should connect.",
            PORT,
        )
    kw: dict = {
        "log_level": "info",
        # Tailscale Serve (and similar) terminate TLS and proxy HTTP to loopback with
        # X-Forwarded-Proto / Host so redirects and absolute URLs match the public origin.
        "proxy_headers": True,
        "forwarded_allow_ips": "127.0.0.1,::1",
    }
    if use_tls:
        kw["ssl_certfile"] = str(cert_path)
        kw["ssl_keyfile"] = str(key_path)
    uvicorn.run(app, host=HOST, port=PORT, **kw)
