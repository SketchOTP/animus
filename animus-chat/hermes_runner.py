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
