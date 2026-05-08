"""Shared PATH fallbacks for subprocesses with minimal inherited PATH.

Used by browser CLI discovery, local terminal environments, and gateway
service unit generation so Homebrew, Termux, and FHS directories stay aligned.
"""

from __future__ import annotations

import functools
import os

# Order: Termux, Apple Silicon Homebrew, then typical FHS layout.
SANE_PATH_DIRS: tuple[str, ...] = (
    "/data/data/com.termux/files/usr/bin",
    "/data/data/com.termux/files/usr/sbin",
    "/opt/homebrew/bin",
    "/opt/homebrew/sbin",
    "/usr/local/sbin",
    "/usr/local/bin",
    "/usr/sbin",
    "/usr/bin",
    "/sbin",
    "/bin",
)

SANE_PATH = os.pathsep.join(SANE_PATH_DIRS)


def extended_sane_path_dirs(*extra_prefix: str) -> list[str]:
    """Return ordered PATH segments: *extra_prefix*, Homebrew node@* bins, then :data:`SANE_PATH_DIRS`.

    Empty strings in *extra_prefix* are skipped.  Later duplicates (by string
    identity) are omitted so callers may prepend project-specific dirs and
    merge with ``dict.fromkeys`` against an inherited PATH.
    """
    out: list[str] = []
    seen: set[str] = set()
    for part in extra_prefix:
        if part and part not in seen:
            seen.add(part)
            out.append(part)
    for part in discover_homebrew_node_dirs():
        if part not in seen:
            seen.add(part)
            out.append(part)
    for part in SANE_PATH_DIRS:
        if part not in seen:
            seen.add(part)
            out.append(part)
    return out


@functools.lru_cache(maxsize=1)
def discover_homebrew_node_dirs() -> tuple[str, ...]:
    """Find Homebrew versioned Node.js bin directories (e.g. node@20, node@24).

    When Node is installed via ``brew install node@24`` and NOT linked into
    ``/opt/homebrew/bin``, Node CLIs are not on the default PATH.  These
    directories are prepended (with :func:`SANE_PATH_DIRS`) via
    :func:`extended_sane_path_dirs` for browser and gateway service generation.
    """
    dirs: list[str] = []
    homebrew_opt = "/opt/homebrew/opt"
    if not os.path.isdir(homebrew_opt):
        return tuple(dirs)
    try:
        for entry in os.listdir(homebrew_opt):
            if entry.startswith("node") and entry != "node":
                bin_dir = os.path.join(homebrew_opt, entry, "bin")
                if os.path.isdir(bin_dir):
                    dirs.append(bin_dir)
    except OSError:
        pass
    return tuple(dirs)
