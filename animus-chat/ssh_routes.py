"""Global SSH host registry + connection test (Phase 7)."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from hermes_runner import chat_data_dir

log = logging.getLogger("animus.ssh")

_ALIAS_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
_HOST_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9]$|^[A-Za-z0-9]$")
_USER_SAFE = re.compile(r"^[a-zA-Z0-9._-]+$")


def _hosts_path() -> Path:
    return chat_data_dir() / "ssh_hosts.json"


def _animus_env_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    p = root / "animus.env"
    return p


def _read_env_kv() -> dict[str, str]:
    p = _animus_env_path()
    kv: dict[str, str] = {}
    if not p.is_file():
        return kv
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            kv[k.strip()] = v.strip()
    return kv


def _upsert_env_line(key: str, value: str) -> None:
    """Set or remove one ``KEY=value`` line in ``animus.env`` (preserves other lines)."""
    p = _animus_env_path()
    lines: list[str] = []
    if p.is_file():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    seen = False
    prefix = f"{key}="
    for line in lines:
        s = line.strip()
        if s.startswith(prefix) or (s and not s.startswith("#") and s.split("=", 1)[0].strip() == key):
            seen = True
            if value:
                out.append(f"{key}={value}")
            continue
        out.append(line)
    if not seen and value:
        out.append(f"{key}={value}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _password_env_key(alias: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]", "_", alias.strip()).upper()
    return f"SSH_PASSWORD_{safe}"


def _read_hosts() -> list[dict[str, Any]]:
    p = _hosts_path()
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return raw if isinstance(raw, list) else []


def _write_hosts(hosts: list[dict[str, Any]]) -> None:
    p = _hosts_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(hosts, indent=2), encoding="utf-8")


def _strip_secrets(h: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in h.items() if k != "password"}
    return out


def _find_host(hosts: list[dict[str, Any]], alias: str) -> dict[str, Any] | None:
    a = alias.strip()
    for h in hosts:
        if str(h.get("alias") or "").strip() == a:
            return h
    return None


async def ssh_hosts_get(_: Request) -> JSONResponse:
    return JSONResponse([_strip_secrets(h) for h in _read_hosts()])


async def ssh_hosts_post(req: Request) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"error": "invalid json"}, status_code=400)
    alias = str(body.get("alias") or "").strip()
    if not _ALIAS_RE.match(alias):
        return JSONResponse({"error": "invalid alias"}, status_code=400)
    hosts = _read_hosts()
    if _find_host(hosts, alias):
        return JSONResponse({"error": "alias already exists"}, status_code=409)
    host = str(body.get("hostname") or "").strip()
    user = str(body.get("user") or "").strip()
    if not host or not user:
        return JSONResponse({"error": "hostname and user required"}, status_code=400)
    rec: dict[str, Any] = {
        "alias": alias,
        "hostname": host,
        "user": user,
        "auth_method": str(body.get("auth_method") or "key").strip().lower() or "key",
        "key_path": str(body.get("key_path") or "~/.ssh/id_rsa").strip(),
        "identities_only": bool(body.get("identities_only")),
        "strict_host_key_checking": body.get("strict_host_key_checking", True),
        "port": int(body.get("port") or 22),
    }
    if rec["port"] < 1 or rec["port"] > 65535:
        return JSONResponse({"error": "invalid port"}, status_code=400)
    pwd = str(body.get("password") or "").strip()
    hosts.append(_strip_secrets(rec))
    _write_hosts(hosts)
    if pwd and rec["auth_method"] == "password":
        pk = _password_env_key(alias)
        _upsert_env_line(pk, pwd)
        os.environ[pk] = pwd
    return JSONResponse({"ok": True, "host": _strip_secrets(rec)})


async def ssh_hosts_put(req: Request) -> JSONResponse:
    alias_q = urllib.parse.unquote(req.path_params.get("alias") or "")
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"error": "invalid json"}, status_code=400)
    hosts = _read_hosts()
    idx = next((i for i, h in enumerate(hosts) if str(h.get("alias") or "").strip() == alias_q), None)
    if idx is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    cur = dict(hosts[idx])
    for k in ("hostname", "user", "auth_method", "key_path", "identities_only", "strict_host_key_checking", "port"):
        if k in body:
            cur[k] = body[k]
    if "port" in cur:
        try:
            p = int(cur["port"])
            if p < 1 or p > 65535:
                raise ValueError
            cur["port"] = p
        except (TypeError, ValueError):
            return JSONResponse({"error": "invalid port"}, status_code=400)
    hosts[idx] = _strip_secrets(cur)
    _write_hosts(hosts)
    if "password" in body:
        pwd = str(body.get("password") or "").strip()
        key = _password_env_key(alias_q)
        if pwd:
            _upsert_env_line(key, pwd)
            os.environ[key] = pwd
        else:
            _upsert_env_line(key, "")
            os.environ.pop(key, None)
    return JSONResponse({"ok": True, "host": _strip_secrets(cur)})


async def ssh_hosts_delete(req: Request) -> JSONResponse:
    alias_q = urllib.parse.unquote(req.path_params.get("alias") or "")
    old = _read_hosts()
    hosts = [h for h in old if str(h.get("alias") or "").strip() != alias_q]
    if len(hosts) == len(old):
        return JSONResponse({"error": "not found"}, status_code=404)
    _write_hosts(hosts)
    key = _password_env_key(alias_q)
    _upsert_env_line(key, "")
    os.environ.pop(key, None)
    return JSONResponse({"ok": True})


def _run_ssh_probe(
    *,
    user: str,
    hostname: str,
    port: int,
    auth_method: str,
    key_path: str,
    identities_only: bool,
    strict_host_key_checking: bool,
    password: str | None,
) -> tuple[bool, str]:
    if not _USER_SAFE.match(user):
        return False, "invalid user"
    if not _HOST_SAFE.match(hostname):
        return False, "invalid hostname"
    base_ssh = [
        "ssh",
        "-o",
        "ConnectTimeout=8",
        "-o",
        "BatchMode=yes",
    ]
    if not strict_host_key_checking:
        base_ssh.extend(["-o", "StrictHostKeyChecking=no"])
    else:
        base_ssh.extend(["-o", "StrictHostKeyChecking=accept-new"])
    if identities_only:
        base_ssh.append("-o")
        base_ssh.append("IdentitiesOnly=yes")
    if port and port != 22:
        base_ssh.extend(["-p", str(port)])
    if auth_method == "key" and key_path:
        kp = Path(key_path).expanduser()
        try:
            kp = kp.resolve()
        except OSError:
            return False, "could not resolve key path"
        if not kp.is_file():
            return False, "identity file not found"
        base_ssh.extend(["-i", str(kp)])
    target = f"{user}@{hostname}"
    cmd = base_ssh + [target, "echo", "ok"]
    env = os.environ.copy()
    try:
        if auth_method == "password" and password:
            sshpass = shutil.which("sshpass")
            if not sshpass:
                return False, "sshpass not installed (required for password auth)"
            env["SSHPASS"] = password
            cmd = [sshpass, "-e"] + cmd
        proc = subprocess.run(  # exempt: ssh connectivity probe
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, "ssh timed out"
    except OSError as exc:
        return False, str(exc)
    if proc.returncode == 0:
        return True, ""
    err = (proc.stderr or proc.stdout or "").strip() or f"exit {proc.returncode}"
    return False, err[:800]


async def ssh_test_post(req: Request) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "invalid json"}, status_code=400)
    alias = str(body.get("alias") or "").strip()
    if alias:
        h = _find_host(_read_hosts(), alias)
        if not h:
            return JSONResponse({"ok": False, "error": "unknown alias"}, status_code=404)
        pwd_key = _password_env_key(alias)
        pwd = (_read_env_kv().get(pwd_key) or os.environ.get(pwd_key) or "").strip() or None
        ok, err = _run_ssh_probe(
            user=str(h.get("user") or ""),
            hostname=str(h.get("hostname") or ""),
            port=int(h.get("port") or 22),
            auth_method=str(h.get("auth_method") or "key"),
            key_path=str(h.get("key_path") or ""),
            identities_only=bool(h.get("identities_only")),
            strict_host_key_checking=bool(h.get("strict_host_key_checking", True)),
            password=pwd if str(h.get("auth_method") or "") == "password" else None,
        )
        return JSONResponse({"ok": ok, "error": err or None})
    user = str(body.get("user") or "").strip()
    host = str(body.get("hostname") or body.get("host") or "").strip()
    try:
        port = int(body.get("port") or 22)
    except (TypeError, ValueError):
        port = 22
    ok, err = _run_ssh_probe(
        user=user,
        hostname=host,
        port=port,
        auth_method=str(body.get("auth_method") or "key").strip().lower() or "key",
        key_path=str(body.get("key_path") or body.get("identity_file") or "").strip(),
        identities_only=bool(body.get("identities_only")),
        strict_host_key_checking=bool(body.get("strict_host_key_checking", True)),
        password=str(body.get("password") or "").strip() or None,
    )
    return JSONResponse({"ok": ok, "error": err or None})


def ssh_route_table():
    from starlette.routing import Route

    return [
        Route("/api/ssh/hosts", ssh_hosts_get, methods=["GET"]),
        Route("/api/ssh/hosts", ssh_hosts_post, methods=["POST"]),
        Route("/api/ssh/hosts/{alias}", ssh_hosts_put, methods=["PUT"]),
        Route("/api/ssh/hosts/{alias}", ssh_hosts_delete, methods=["DELETE"]),
        Route("/api/ssh/test", ssh_test_post, methods=["POST"]),
    ]
