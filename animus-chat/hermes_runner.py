"""Single subprocess entrypoint for the ``hermes`` CLI (ANIMUS control plane)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("animus.hermes")

# Cache API_SERVER_KEY read from Hermes ~/.hermes/.env (mtime-aware) so chat streaming
# does not re-parse the file on every SSE chunk.
_dotenv_bearer_cache: tuple[str, float, str] | None = None  # (resolved_path, mtime, bearer)
_logged_api_server_fallback = False


def chat_data_dir() -> Path:
    """Hermes Chat / ANIMUS conversation + ``config.json`` directory (matches ``server.DATA_DIR``)."""
    for key in ("CHAT_DATA_DIR", "HERMES_CHAT_DATA_DIR"):
        raw = (os.getenv(key) or "").strip()
        if raw:
            p = Path(raw).expanduser().resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.is_file():
        try:
            text = env_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, _, v = s.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k in ("CHAT_DATA_DIR", "HERMES_CHAT_DATA_DIR") and v:
                p = Path(v).expanduser().resolve()
                p.mkdir(parents=True, exist_ok=True)
                return p
    p = (Path.home() / ".hermes" / "chat").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir() -> Path:
    """Package-relative data (audits, caches). Prefer ``chat_data_dir()`` for user-facing state."""
    base = (os.getenv("DATA_DIR") or os.getenv("CHAT_DATA_DIR") or os.getenv("HERMES_CHAT_DATA_DIR") or "./data").strip()
    p = Path(base).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _parse_env_file_key(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return ""


def _hermes_dotenv_candidates() -> list[Path]:
    """Paths that may define ``API_SERVER_KEY`` for the local Hermes gateway."""
    seen: set[str] = set()
    out: list[Path] = []

    def add(p: Path) -> None:
        try:
            k = str(p.resolve())
        except OSError:
            k = str(p)
        if k not in seen:
            seen.add(k)
            out.append(p)

    hh = (os.getenv("HERMES_HOME") or "").strip()
    if hh:
        hp = Path(hh).expanduser().resolve()
        if hp.parent.name == "profiles":
            add(hp.parent.parent / ".env")
        env_in_profile = hp / ".env"
        if env_in_profile.is_file():
            add(env_in_profile)
    add(Path.home() / ".hermes" / ".env")
    return out


def _api_server_key_from_hermes_dotenv() -> str:
    """Return ``API_SERVER_KEY`` from Hermes env files when ``HERMES_API_KEY`` is unset."""
    global _dotenv_bearer_cache, _logged_api_server_fallback
    for path in _hermes_dotenv_candidates():
        if not path.is_file():
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        key = str(path.resolve())
        if _dotenv_bearer_cache and _dotenv_bearer_cache[0] == key and _dotenv_bearer_cache[1] == st.st_mtime:
            return _dotenv_bearer_cache[2]
        tok = _parse_env_file_key(path, "API_SERVER_KEY")
        if tok:
            _dotenv_bearer_cache = (key, st.st_mtime, tok)
            if not _logged_api_server_fallback:
                _logged_api_server_fallback = True
                log.info(
                    "HERMES_API_KEY unset — using API_SERVER_KEY from %s for gateway Authorization "
                    "(set HERMES_API_KEY in animus.env to override or to match a remote gateway).",
                    path,
                )
            return tok
    _dotenv_bearer_cache = None
    return ""


def gateway_api_bearer() -> str:
    """Bearer token for the Hermes OpenAI-compatible gateway (``HERMES_API_KEY``).

    If ``HERMES_API_KEY`` is unset or blank, reads ``API_SERVER_KEY`` from the same
    ``~/.hermes/.env`` file Hermes uses for the gateway — avoids duplicate secrets and
    401 \"Invalid API key\" for typical local installs.

    Read from ``os.environ`` first each call so ``POST /api/setup/save-config`` updates apply
    without restarting the chat server.
    """
    tok = (os.getenv("HERMES_API_KEY") or "").strip()
    if tok:
        return tok
    return _api_server_key_from_hermes_dotenv().strip()


def gateway_bearer_source() -> str:
    """Where ``gateway_api_bearer()`` came from: ``hermes_api_key`` | ``hermes_dotenv`` | ``none``."""
    if (os.getenv("HERMES_API_KEY") or "").strip():
        return "hermes_api_key"
    if _api_server_key_from_hermes_dotenv():
        return "hermes_dotenv"
    return "none"


def gateway_upstream_headers(*, content_type_json: bool = True) -> dict[str, str]:
    """Headers for ``httpx`` calls to ``HERMES_API_URL``; omit ``Authorization`` when the bearer is empty."""
    h: dict[str, str] = {}
    tok = gateway_api_bearer()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    if content_type_json:
        h["Content-Type"] = "application/json"
    return h


def get_hermes_bin() -> str:
    env_bin = (os.getenv("HERMES_BIN") or "").strip()
    if env_bin:
        return env_bin
    found = shutil.which("hermes")
    if found:
        return found
    raise RuntimeError("hermes binary not found. Install Hermes Agent or set HERMES_BIN.")


def run_hermes(args: list[str], timeout: int = 30) -> dict[str, Any]:
    """Run ``hermes <args>`` and return a structured result."""
    cmd = [get_hermes_bin()] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": result.returncode == 0,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        log.error("hermes %s timed out after %ss", args, timeout)
        return {"ok": False, "stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "hermes binary not found", "returncode": -1}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "stdout": "", "stderr": str(exc), "returncode": -1}


def run_hermes_cron(args: list[str], timeout: int = 30) -> dict[str, Any]:
    """Run ``hermes cron <args>`` (same semantics as ``run_hermes``)."""
    return run_hermes(["cron"] + list(args), timeout=timeout)


def append_audit(rel_name: str, line: str) -> None:
    path = chat_data_dir() / rel_name
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts} {line}\n")
