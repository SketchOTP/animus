"""
Local Hermes stack: gateway (API + messaging) + optional Hermes Chat PWA.

Commands: ``hermes run``, ``hermes restart``, ``hermes stop``.

Chat is started via user systemd (``hermes-chat.service``) when that unit file
exists; otherwise a discovered ``hermes-chat`` checkout is started manually with
``hermes-chat.env`` loaded (same as systemd ``EnvironmentFile``).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHAT_SYSTEMD_UNIT = "hermes-chat.service"


def resolve_chat_root() -> Path | None:
    """Return the Hermes Chat checkout directory, or None if unknown."""
    raw = (os.environ.get("HERMES_CHAT_ROOT") or "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        if (p / "server.py").is_file():
            return p
        return None
    sibling = PROJECT_ROOT.parent / "hermes-chat"
    if (sibling / "server.py").is_file():
        return sibling.resolve()
    return None


def chat_user_unit_path() -> Path:
    return Path.home() / ".config" / "systemd" / "user" / CHAT_SYSTEMD_UNIT


def chat_env_path(chat_root: Path | None) -> Path | None:
    if chat_root is None:
        return None
    p = chat_root / "hermes-chat.env"
    return p if p.is_file() else None


def _read_chat_port(chat_root: Path | None) -> int:
    envp = chat_env_path(chat_root)
    if envp:
        try:
            for line in envp.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("CHAT_PORT=") and "=" in line:
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    return int(val)
        except (OSError, ValueError):
            pass
    try:
        return int(os.environ.get("CHAT_PORT", "3000"))
    except ValueError:
        return 3000


def _pids_listening_on_tcp_port(port: int) -> list[int]:
    """Best-effort PIDs from ``ss -tlnp`` for a local TCP port."""
    pids: list[int] = []
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return pids
    if result.returncode != 0 or not result.stdout:
        return pids
    needle = f":{port}"
    for line in result.stdout.splitlines():
        if needle not in line or "LISTEN" not in line:
            continue
        for m in re.finditer(r"pid=(\d+)", line):
            try:
                pids.append(int(m.group(1)))
            except ValueError:
                pass
    return sorted(set(pids))


def _chat_health_ok(port: int, timeout: float = 2.0) -> bool:
    try:
        import urllib.request

        url = f"http://127.0.0.1:{port}/api/health"
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


def _terminate_pid(pid: int, *, grace: float = 2.0) -> None:
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        return
    except PermissionError:
        return
    deadline = time.time() + grace
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        except OSError:
            return
        time.sleep(0.15)
    try:
        os.kill(pid, 9)
    except (ProcessLookupError, PermissionError):
        pass


def _gateway_unit_installed() -> bool:
    from hermes_cli.gateway import get_systemd_unit_path

    return get_systemd_unit_path(system=False).exists() or get_systemd_unit_path(
        system=True
    ).exists()


def _start_gateway_managed() -> bool:
    from hermes_cli.gateway import (
        get_launchd_plist_path,
        is_macos,
        is_termux,
        is_wsl,
        launchd_start,
        supports_systemd_services,
        systemd_start,
    )

    if is_termux():
        print("hermes run: Termux has no stack services — use `hermes gateway run`", file=sys.stderr)
        return False
    if supports_systemd_services():
        if not _gateway_unit_installed():
            print(
                "hermes run: no gateway systemd unit found. Install with:\n"
                "  hermes gateway install",
                file=sys.stderr,
            )
            return False
        systemd_start(system=False)
        return True
    if is_macos():
        if not get_launchd_plist_path().exists():
            print(
                "hermes run: no gateway LaunchAgent found. Install with:\n"
                "  hermes gateway install",
                file=sys.stderr,
            )
            return False
        launchd_start()
        return True
    if is_wsl():
        print(
            "hermes run: systemd is not available in this WSL session.\n"
            "  Use:  hermes gateway run\n"
            "  Or enable systemd in /etc/wsl.conf and restart WSL.",
            file=sys.stderr,
        )
        return False
    print(
        "hermes run: no supported service manager for the gateway on this platform.",
        file=sys.stderr,
    )
    return False


def _stop_gateway_managed() -> bool:
    from hermes_cli.gateway import (
        get_launchd_plist_path,
        is_macos,
        supports_systemd_services,
        systemd_stop,
        launchd_stop,
    )

    if supports_systemd_services() and _gateway_unit_installed():
        try:
            systemd_stop(system=False)
            return True
        except subprocess.CalledProcessError:
            return False
    if is_macos() and get_launchd_plist_path().exists():
        try:
            launchd_stop()
            return True
        except subprocess.CalledProcessError:
            return False
    return False


def _chat_systemd_user_available() -> bool:
    return chat_user_unit_path().is_file()


def _run_user_systemctl(args: list[str], *, check: bool) -> subprocess.CompletedProcess:
    from hermes_cli.gateway import _ensure_user_systemd_env, _run_systemctl

    _ensure_user_systemd_env()
    return _run_systemctl(args, system=False, check=check, timeout=90)


def _start_chat_managed() -> bool:
    if not _chat_systemd_user_available():
        return False
    _run_user_systemctl(["start", "hermes-chat"], check=True)
    print("✓ User systemd service started: hermes-chat")
    return True


def _stop_chat_managed() -> bool:
    if not _chat_systemd_user_available():
        return False
    r = _run_user_systemctl(["stop", "hermes-chat"], check=False)
    if r.returncode == 0:
        print("✓ User systemd service stopped: hermes-chat")
        return True
    return False


def _start_chat_manual(chat_root: Path) -> bool:
    env_file = chat_env_path(chat_root)
    if not env_file:
        print(
            f"hermes run: missing {chat_root / 'hermes-chat.env'} — "
            "cannot start chat without API key / config.",
            file=sys.stderr,
        )
        return False
    port = _read_chat_port(chat_root)
    if _chat_health_ok(port):
        print(f"✓ Hermes Chat already responding on port {port}")
        return True
    try:
        from dotenv import dotenv_values
    except ImportError:
        print("hermes run: python-dotenv is required for manual chat start.", file=sys.stderr)
        return False

    vals = dotenv_values(env_file)
    child_env = os.environ.copy()
    for k, v in vals.items():
        if v is not None and k:
            child_env[k] = v
    if not (child_env.get("HERMES_API_KEY") or "").strip():
        print(
            "hermes run: HERMES_API_KEY is empty after loading hermes-chat.env — "
            "fix the file (must match API_SERVER_KEY in Hermes .env).",
            file=sys.stderr,
        )
        return False
    log_dir = Path.home() / ".hermes" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "hermes-chat-manual.log"
    log_fd = os.open(str(log_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        proc = subprocess.Popen(
            [sys.executable, str(chat_root / "server.py")],
            cwd=str(chat_root),
            env=child_env,
            stdout=log_fd,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        os.close(log_fd)
    for _ in range(30):
        time.sleep(0.2)
        if _chat_health_ok(port, timeout=1.5):
            print(f"✓ Hermes Chat started manually (port {port}, log {log_path})")
            return True
        if proc.poll() is not None:
            print(
                f"hermes run: chat server exited early (code {proc.returncode}). "
                f"See {log_path}",
                file=sys.stderr,
            )
            return False
    print(
        f"hermes run: chat did not become healthy on port {port} in time. See {log_path}",
        file=sys.stderr,
    )
    return False


def _sweep_manual_chat_listeners(chat_root: Path | None) -> int:
    """SIGTERM PIDs listening on the chat port that look like ``server.py`` runs."""
    port = _read_chat_port(chat_root)
    killed = 0
    for pid in _pids_listening_on_tcp_port(port):
        try:
            raw = Path(f"/proc/{pid}/cmdline").read_bytes()
        except OSError:
            continue
        try:
            cmd = raw.replace(b"\0", b" ").decode("utf-8", errors="ignore")
        except Exception:
            continue
        if "server.py" not in cmd:
            continue
        if chat_root is not None and str(chat_root) not in cmd and "hermes-chat" not in cmd:
            continue
        print(f"Stopping stray Hermes Chat listener PID {pid} (port {port})")
        _terminate_pid(pid)
        killed += 1
    return killed


def run_stack() -> int:
    from hermes_cli.gateway import supports_systemd_services

    chat_root = resolve_chat_root()
    if not _start_gateway_managed():
        return 1
    if supports_systemd_services() and _chat_systemd_user_available():
        if not _start_chat_managed():
            return 1
    elif chat_root is not None:
        if not _start_chat_manual(chat_root):
            return 1
    else:
        print(
            "Note: Hermes Chat not started (no user unit at "
            f"{chat_user_unit_path()} and no checkout beside this repo). "
            "Set HERMES_CHAT_ROOT or install ~/.config/systemd/user/hermes-chat.service",
        )
    return 0


def stop_stack(*, sweep_chat: bool = True) -> int:
    from hermes_cli.gateway import supports_systemd_services

    chat_root = resolve_chat_root()
    stopped_any = False
    if supports_systemd_services() and _chat_systemd_user_available():
        if _stop_chat_managed():
            stopped_any = True

    if _stop_gateway_managed():
        stopped_any = True

    if sweep_chat and chat_root is not None:
        time.sleep(0.5)
        stopped_any = stopped_any or _sweep_manual_chat_listeners(chat_root) > 0

    if not stopped_any:
        print(
            "hermes stop: no managed gateway/chat services found. "
            "If the gateway runs in a terminal, press Ctrl+C or use "
            "`hermes gateway stop --all`.",
            file=sys.stderr,
        )
        return 1
    return 0


def restart_stack() -> int:
    rc = stop_stack(sweep_chat=True)
    if rc != 0:
        pass
    time.sleep(2)
    return run_stack()
