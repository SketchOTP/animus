#!/usr/bin/env python3
"""If animus.env leaves HERMES_API_KEY empty but ~/.hermes/.env defines API_SERVER_KEY, copy it.

Hermes gateway auth uses API_SERVER_KEY; ANIMUS must send the same value as HERMES_API_KEY
or clients get 401 Invalid API key. Runtime code in hermes_runner also reads ~/.hermes/.env,
but writing animus.env keeps systemd EnvironmentFile self-contained for buyers."""
from __future__ import annotations

import sys
from pathlib import Path


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def _set_or_append_hermes_api_key(animus_env: Path, value: str) -> bool:
    """Return True if animus.env was modified."""
    if not animus_env.is_file():
        return False
    raw = animus_env.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines(keepends=True)
    new_lines: list[str] = []
    found = False
    changed = False
    for line in lines:
        if line.lstrip().startswith("HERMES_API_KEY="):
            found = True
            cur = line.split("=", 1)[-1].strip().rstrip("\r\n")
            cur = cur.strip().strip('"').strip("'")
            if cur:
                return False  # already set — do not overwrite
            rep = f"HERMES_API_KEY={value}\n"
            if line != rep:
                changed = True
            new_lines.append(rep)
        else:
            new_lines.append(line)
    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"HERMES_API_KEY={value}\n")
        changed = True
    if changed:
        animus_env.write_text("".join(new_lines), encoding="utf-8")
    return changed


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: merge-hermes-gateway-auth.py /path/to/animus.env", file=sys.stderr)
        return 2
    animus_env = Path(sys.argv[1]).expanduser().resolve()
    hermes_dot = Path.home() / ".hermes" / ".env"
    if not hermes_dot.is_file():
        return 0
    hd = _parse_env_file(hermes_dot)
    api_key = (hd.get("API_SERVER_KEY") or "").strip()
    if not api_key:
        return 0
    if not animus_env.is_file():
        return 0
    ad = _parse_env_file(animus_env)
    if (ad.get("HERMES_API_KEY") or "").strip():
        return 0
    if _set_or_append_hermes_api_key(animus_env, api_key):
        print(f"Set HERMES_API_KEY in {animus_env} from ~/.hermes/.env API_SERVER_KEY (gateway auth).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
