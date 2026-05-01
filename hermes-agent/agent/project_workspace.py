"""Workspace markdown files for Hermes Chat project folders (history, repo map, notes, goal).

Used by ``hermes project …`` CLI, Hermes Chat server routes, and cron delivery.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

HISTORY_FILENAME = "project_history.md"
REPO_MAP_FILENAME = "repo_map.md"
NOTES_FILENAME = "notes.md"
GOAL_FILENAME = "project_goal.md"
STATUS_FILENAME = "project_status.md"
KNOWLEDGE_FILENAME = "project_knowledge.md"
PROJECT_MEMORY_DIRNAME = "project_memory"
PROJECT_MEMORY_INDEX_FILENAME = "index.json"
SETUP_REPO_FILENAME = "setup_repo.md"
AGENTS_MD_FILENAME = "AGENTS.md"
CLAUDE_MD_FILENAME = "CLAUDE.md"
CURSOR_RULES_FILENAME = ".cursorrules"
# Optional: absolute path to a ``setup_repo.md`` template Hermes Chat copies into each
# registered project root when that file is missing (see ``ensure_workspace_files``).
HERMES_CHAT_SETUP_REPO_MD_ENV = "HERMES_CHAT_SETUP_REPO_MD"
HERMES_CHAT_POLICY_TEMPLATE_ENV = "HERMES_CHAT_POLICY_TEMPLATE"

_AGENT_BOOTSTRAP_SENTINEL = "<!-- hermes-chat-setup-repo-bootstrap -->"
_COMPACT_MEMORY_POLICY_SENTINEL = "<!-- hermes-project-memory-v1 -->"

HISTORY_HEADER = """# Project history

One line per event. Format: ``HHMM MMDDYY — summary`` (local time).

Updated by Hermes Chat, scheduled cron runs, and ``hermes project history-append``.

"""

REPO_MAP_HEADER = """# Repository map

Auto-generated index of files under this project (depth- and size-limited).
Regenerate with ``hermes project repo-map-refresh --path …``, ``hermes project repo-maps-refresh-all`` (cron), or **↻ Map** in Hermes Chat.

"""

NOTES_HEADER = """# Notes

Operator notes for this project (Markdown). Edited in Hermes Chat under **Project workspace → Notes**.

"""

GOAL_HEADER = """# Project goal

North-star intent for this repository. Keep it short and revisable. Edited in Hermes Chat under **Project workspace → Goal**.

"""

STATUS_HEADER = """# Project status

Current snapshot for this repository:
- current state
- active goal
- in-progress work
- blockers / risks
- latest validation status

"""

KNOWLEDGE_HEADER = """# Project knowledge

Durable lessons for future agents. Keep this short and practical. Avoid task logs; record conventions, pitfalls, and reusable validation tips.

"""

_DEFAULT_POLICY_TEMPLATE = """---
description: Mandatory operating rules for AI coding agents in this repository.
alwaysApply: true
---

Before changing code, read:
- `project_goal.md`
- `project_status.md`
- `project_history.md`
- `project_knowledge.md`
- `repo_map.md`

After meaningful work, update:
- `project_status.md`
- `project_history.md` (append one entry with files touched)
- `project_knowledge.md`
- `repo_map.md` (when structure/ownership changes)

Keep changes minimal, avoid unrelated edits, and do not run destructive commands without explicit approval.

<!-- hermes-project-memory-v1 -->
Compact project memory workflow:
- Read `project_memory/index.json` first for token-light navigation.
- Use `repo_map.md` as human-readable backup, not the primary full context payload.
- Do not load full `project_history.md` by default; only recent tail entries when needed.
- Keep `project_memory/index.json` current after structural changes.
"""

_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        ".eggs",
        ".idea",
        ".vscode",
    }
)

_MAX_REPO_FILES = 650
_MAX_TEXT_BYTES = 48_000
_MAX_SUMMARY_LEN = 160


def hermes_chat_data_dir() -> Path:
    """Hermes Chat server data root (``conversations.json``, ``projects.json``).

    Same resolution as ``cron/hermes_chat_delivery`` so cron delivery and
    ``project_history`` see the same files as ``hermes-chat/server.py``.

    Order: ``CHAT_DATA_DIR``, ``HERMES_CHAT_DATA_DIR``, then those keys from
    ``~/.hermes/.env`` if unset in the environment, else ``~/.hermes/chat``.
    """
    for key in ("CHAT_DATA_DIR", "HERMES_CHAT_DATA_DIR"):
        raw = (os.environ.get(key) or "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    try:
        from dotenv import dotenv_values

        env_path = Path.home() / ".hermes" / ".env"
        if env_path.is_file():
            vals = dotenv_values(env_path) or {}
            for key in ("CHAT_DATA_DIR", "HERMES_CHAT_DATA_DIR"):
                raw = (vals.get(key) or "").strip()
                if raw:
                    p = Path(raw).expanduser().resolve()
                    logger.info(
                        "hermes_chat_data_dir from %s (%s=%s); export the same in "
                        "gateway/cron if jobs should not depend on this file read",
                        env_path,
                        key,
                        p,
                    )
                    return p
    except Exception as exc:
        logger.debug("hermes_chat_data_dir dotenv fallback skipped: %s", exc)
    return (Path.home() / ".hermes" / "chat").resolve()


def hermes_projects_sync_root() -> Path:
    """Default Hermes Chat projects parent (``~/Projects`` or env override).

    Used to avoid scanning the whole sync directory or an ancestor of it when
    bulk-refreshing ``repo_map.md`` from ``projects.json``.
    """
    raw = (os.environ.get("HERMES_CHAT_PROJECTS_SYNC_ROOT") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / "Projects").resolve()


def _unsafe_bulk_repo_map_root(root: Path) -> bool:
    """True if *root* is the sync parent or a strict ancestor of it (multi-repo)."""
    try:
        rr = root.resolve()
        sync = hermes_projects_sync_root()
    except OSError:
        return True
    if rr == sync:
        return True
    try:
        sync.relative_to(rr)
    except ValueError:
        return False
    return rr != sync


def _normalize_hermes_chat_project_id(project_id: str) -> str:
    t = (project_id or "").strip()
    if len(t) == 36 and t[8] == t[13] == t[18] == t[23] == "-":
        return t.lower()
    return t


def setup_repo_template_path() -> Optional[Path]:
    """Return the bootstrap guide file to copy into project roots, if configured and present."""
    raw = (os.environ.get(HERMES_CHAT_SETUP_REPO_MD_ENV) or "").strip()
    if not raw:
        return None
    try:
        p = Path(raw).expanduser().resolve()
    except OSError:
        return None
    return p if p.is_file() else None


def workspace_files_path_raw(item: dict) -> str:
    """Directory for ``project_history.md`` / ``repo_map.md`` (optional override)."""
    w = str(item.get("workspace_files_path") or "").strip()
    if w:
        return w
    return str(item.get("path") or "").strip()


def read_hermes_chat_project_paths_by_id() -> dict[str, str]:
    """Map Hermes Chat project ``id`` → absolute path for workspace files.

    Uses ``workspace_files_path`` when set (e.g. sshfs mount of the real repo),
    otherwise ``path``.
    """
    p = hermes_chat_data_dir() / "projects.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, str] = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("id"):
                raw = workspace_files_path_raw(item)
                if not raw:
                    continue
                pid = _normalize_hermes_chat_project_id(str(item["id"]))
                out[pid] = raw
    return out


def iter_hermes_chat_project_roots() -> list[Path]:
    """Unique resolved directories listed in ``projects.json`` (existing dirs only)."""
    out: list[Path] = []
    seen: set[Path] = set()
    for raw in read_hermes_chat_project_paths_by_id().values():
        t = (raw or "").strip()
        if not t:
            continue
        try:
            r = Path(t).expanduser().resolve()
        except OSError:
            continue
        if not r.is_dir() or r in seen:
            continue
        seen.add(r)
        out.append(r)
    out.sort(key=lambda p: str(p).lower())
    return out


def resolve_project_root_from_hermes_chat_id(project_id: str) -> Optional[Path]:
    tid = _normalize_hermes_chat_project_id(str(project_id or ""))
    if not tid:
        return None
    raw = read_hermes_chat_project_paths_by_id().get(tid)
    if not raw:
        return None
    try:
        root = Path(raw).expanduser().resolve()
    except Exception:
        return None
    return root if root.is_dir() else None


def normalize_project_root(raw: str | Path) -> Path:
    p = Path(raw).expanduser().resolve()
    if not p.is_dir():
        raise ValueError(f"Not a directory: {p}")
    return p


def _try_flock_ex(lock_fd: int) -> bool:
    try:
        import fcntl

        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return True
    except ImportError:
        return False


def _flock_un(lock_fd: int) -> None:
    try:
        import fcntl

        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except ImportError:
        pass


def _format_history_stamp() -> str:
    return datetime.now().astimezone().strftime("%H%M %m%d%y")


def _sanitize_summary(text: str, *, max_len: int = 480) -> str:
    s = " ".join((text or "").replace("\r", " ").replace("\n", " ").split())
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def append_gateway_tool_history_line(
    root: Path,
    tool_name: str,
    tool_args: Any,
    tool_result: Any,
    *,
    source: str = "gateway",
) -> str:
    """Append one line describing a completed tool call (gateway / cron)."""
    from agent.display import _detect_tool_failure

    name = str(tool_name or "tool").strip() or "tool"
    if name.startswith("_"):
        return ""
    try:
        args_s = json.dumps(tool_args, ensure_ascii=False) if tool_args is not None else ""
    except Exception:
        args_s = str(tool_args)
    args_s = " ".join(args_s.split())
    if len(args_s) > 220:
        args_s = args_s[:217] + "…"
    res = str(tool_result if tool_result is not None else "")
    fail, _ = _detect_tool_failure(name, res)
    flag = "error" if fail else "ok"
    res_preview = " ".join(res.split())
    if len(res_preview) > 160:
        res_preview = res_preview[:157] + "…"
    summary = f"Tool {name} ({flag}) {args_s} → {res_preview}"
    return append_project_history_line(normalize_project_root(root), summary, source=source)


def append_project_history_line(
    root: Path,
    summary: str,
    *,
    source: str = "",
) -> str:
    """Append one line to ``project_history.md`` under *root* (creates file if missing).

    Returns the line that was written (without trailing newline).
    """
    root = normalize_project_root(root)
    summary = _sanitize_summary(summary)
    if not summary:
        summary = "(no summary)"
    line = f"{_format_history_stamp()} — {summary}"
    if source:
        src = _sanitize_summary(source, max_len=80)
        if src:
            line += f" ({src})"

    hist = root / HISTORY_FILENAME
    if not hist.exists():
        hist.write_text(HISTORY_HEADER, encoding="utf-8")

    lock_path = hist.parent / (hist.name + ".flock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_f = open(lock_path, "a+", encoding="utf-8")
    try:
        if not _try_flock_ex(lock_f.fileno()):
            logger.warning("project_history: flock unavailable for %s", hist)
        cur = hist.read_text(encoding="utf-8") if hist.exists() else ""
        if cur and not cur.endswith("\n"):
            cur += "\n"
        new_body = cur + line + "\n"
        tmp = hist.parent / (hist.name + ".tmp")
        tmp.write_text(new_body, encoding="utf-8")
        tmp.replace(hist)
    finally:
        _flock_un(lock_f.fileno())
        lock_f.close()
    return line


def append_history_for_cron_delivery(
    project_id: str,
    *,
    job_name: str = "",
    job_id: str = "",
    text_preview: str = "",
) -> None:
    root = resolve_project_root_from_hermes_chat_id(project_id)
    if root is None:
        logger.debug("cron project history: no path for project_id=%s", project_id)
        return
    name = (job_name or job_id or "cron").strip() or "cron"
    pv = _sanitize_summary(text_preview, max_len=200) if text_preview else ""
    summary = f"Cron «{name}» delivered to Hermes Chat"
    if pv:
        summary += f": {pv}"
    src = "cron"
    if job_id:
        src += f" id={job_id}"
    append_project_history_line(root, summary, source=src)


def _is_skippable_dir(name: str) -> bool:
    if name in _SKIP_DIR_NAMES:
        return True
    if name.startswith(".") and name not in {".github"}:
        return True
    return False


def _guess_summary(path: Path) -> str:
    try:
        st = path.stat()
    except OSError:
        return "unreadable"
    if path.is_dir():
        return "directory"
    if not path.is_file():
        return "non-file"
    if st.st_size == 0:
        return "empty file"
    if st.st_size > _MAX_TEXT_BYTES:
        return f"large file ({st.st_size} bytes)"
    suf = path.suffix.lower()
    if suf in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".eot", ".ttf", ".pdf", ".zip", ".gz", ".so", ".o", ".a", ".dylib", ".dll", ".exe"}:
        return f"binary ({suf or 'data'})"
    try:
        raw = path.read_bytes()[:8000]
        if b"\0" in raw[:2048]:
            return "binary"
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return "unreadable"
    one = " ".join(text.splitlines()[:3]).strip()
    one = re.sub(r"\s+", " ", one)
    if not one:
        return f"text file ({st.st_size} bytes)"
    if len(one) > _MAX_SUMMARY_LEN:
        return one[: _MAX_SUMMARY_LEN - 1] + "…"
    return one


def _safe_iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _normalize_memory_text(text: str) -> str:
    t = (text or "").strip()
    if len(t) > 160:
        return t[:157] + "..."
    return t


def _walk_files(root: Path) -> Iterable[Path]:
    n = 0
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        rel_depth = len(dp.relative_to(root).parts) if dp != root else 0
        if rel_depth >= 12:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(d for d in dirnames if not _is_skippable_dir(d))
        for fn in sorted(filenames):
            if fn.startswith(".") and fn not in {".gitignore", ".env.example"}:
                continue
            p = dp / fn
            if not p.is_file():
                continue
            n += 1
            if n > _MAX_REPO_FILES:
                return
            yield p


def _walk_files_for_memory(root: Path, cap: int = 220) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for p in _walk_files(root):
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        rows.append((rel, _normalize_memory_text(_guess_summary(p))))
        if len(rows) >= cap:
            break
    rows.sort(key=lambda x: x[0].lower())
    return rows


def _discover_entrypoints(rows: list[tuple[str, str]]) -> list[dict[str, str]]:
    wanted = (
        "readme.md",
        "server.py",
        "main.py",
        "app.py",
        "index.html",
        "cli.py",
        "run.py",
    )
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for rel, summary in rows:
        low = rel.lower()
        if low in seen:
            continue
        if any(low.endswith(name) for name in wanted):
            out.append({"path": rel, "summary": summary})
            seen.add(low)
        if len(out) >= 16:
            break
    if out:
        return out
    # Fallback: first small set of files so index is never empty.
    return [{"path": rel, "summary": summary} for rel, summary in rows[:12]]


def _discover_areas(rows: list[tuple[str, str]]) -> list[dict[str, Any]]:
    by_top: dict[str, int] = {}
    for rel, _summary in rows:
        top = rel.split("/", 1)[0]
        by_top[top] = by_top.get(top, 0) + 1
    ranked = sorted(by_top.items(), key=lambda x: (-x[1], x[0].lower()))
    return [{"name": name, "file_count": count} for name, count in ranked[:24]]


def generate_project_memory_index(root: Path) -> dict[str, Any]:
    root = normalize_project_root(root)
    rows = _walk_files_for_memory(root)
    index = {
        "schema_version": 1,
        "generated_at": _safe_iso_now(),
        "project_root": str(root),
        "entrypoints": _discover_entrypoints(rows),
        "areas": _discover_areas(rows),
        "files": [{"path": rel, "summary": summary} for rel, summary in rows],
        "commands": [
            "Read project_memory/index.json first",
            "Read repo_map.md only for human-oriented backup detail",
            "Read only recent project_history.md lines when needed",
        ],
    }
    return index


def write_project_memory_index(root: Path, body: dict[str, Any]) -> Path:
    root = normalize_project_root(root)
    mem_dir = root / PROJECT_MEMORY_DIRNAME
    mem_dir.mkdir(parents=True, exist_ok=True)
    target = mem_dir / PROJECT_MEMORY_INDEX_FILENAME
    content = json.dumps(body, ensure_ascii=True, indent=2) + "\n"
    _write_text_atomic(target, content)
    return target


def refresh_project_memory_index(root: Path) -> dict[str, Any]:
    root = normalize_project_root(root)
    body = generate_project_memory_index(root)
    target = write_project_memory_index(root, body)
    return {
        "path": str(root),
        "file": str(target),
        "entries": len(body.get("files") or []),
    }


def _project_memory_index_needs_refresh(path: Path, *, max_age_seconds: int = 6 * 60 * 60) -> bool:
    """True when ``project_memory/index.json`` is missing, stale, or malformed."""
    if not path.is_file():
        return True
    try:
        age = max(0.0, datetime.now().timestamp() - path.stat().st_mtime)
    except OSError:
        return True
    if age > max_age_seconds:
        return True
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return True
    if not isinstance(data, dict):
        return True
    if int(data.get("schema_version") or 0) != 1:
        return True
    if not isinstance(data.get("files"), list):
        return True
    if not isinstance(data.get("entrypoints"), list):
        return True
    return False


def generate_repo_map_markdown(root: Path) -> str:
    root = normalize_project_root(root)
    lines = [REPO_MAP_HEADER.rstrip(), "", f"Root: `{root}`", ""]
    lines.append("## Files")
    lines.append("")
    rows: list[tuple[str, str]] = []
    for p in _walk_files(root):
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            continue
        rows.append((rel, _guess_summary(p)))
    rows.sort(key=lambda x: x[0].lower())
    for rel, summ in rows:
        lines.append(f"- `{rel}` — {summ}")
    lines.append("")
    lines.append(f"*Listed {len(rows)} files (cap {_MAX_REPO_FILES}).*")
    lines.append("")
    return "\n".join(lines)


def write_repo_map(root: Path, content: str) -> None:
    root = normalize_project_root(root)
    path = root / REPO_MAP_FILENAME
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def refresh_repo_map(
    root: Path,
    *,
    ensure_workspace: bool = True,
) -> dict[str, Any]:
    root = normalize_project_root(root)
    ensured: dict[str, Any] = {"created": [], "updated": []}
    if ensure_workspace:
        ensured = ensure_workspace_files(root, generate_repo_map_if_missing=False)
    refresh_project_memory_index(root)
    body = generate_repo_map_markdown(root)
    write_repo_map(root, body)
    return {
        "path": str(root),
        "file": REPO_MAP_FILENAME,
        "bytes": len(body.encode("utf-8")),
        "created": list(ensured.get("created") or []),
        "updated": list(ensured.get("updated") or []),
    }


def refresh_all_hermes_chat_repo_maps(
    *,
    missing_only: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """For each Hermes Chat project path in ``projects.json``:

    1. Resolve to that project directory only (never the sync parent).
    2. Ensure ``project_history.md`` and ``repo_map.md`` exist there (create if missing).
    3. Unless ``missing_only``, regenerate ``repo_map.md`` from the tree.

    Skips the projects sync root and ancestors of it so a mis-set path does not
    walk ``~/Projects`` or ``$HOME`` as one tree.
    """
    results: list[dict[str, Any]] = []
    for root in iter_hermes_chat_project_roots():
        if _unsafe_bulk_repo_map_root(root):
            results.append(
                {
                    "path": str(root),
                    "skipped": "unsafe_workspace",
                    "reason": "sync_root_or_ancestor",
                }
            )
            continue
        if dry_run:
            results.append({"path": str(root), "dry_run": True})
            continue
        ensured = ensure_workspace_files(root, generate_repo_map_if_missing=True)
        row: dict[str, Any] = {
            "path": str(root),
            "created": ensured.get("created", []),
            "project_memory_refreshed": False,
            "repo_map_refreshed": False,
        }
        memory_info = refresh_project_memory_index(root)
        row["project_memory_refreshed"] = True
        row["project_memory_entries"] = int(memory_info.get("entries") or 0)
        if not missing_only:
            map_info = refresh_repo_map(root, ensure_workspace=False)
            row["repo_map_refreshed"] = True
            row["file"] = map_info.get("file")
            row["bytes"] = map_info.get("bytes")
        results.append(row)
    return results


def _maybe_install_setup_repo_and_agent_bootstrap_note(root: Path, created: list[str]) -> None:
    """Copy ``setup_repo.md`` from env template when absent; nudge agents if ``AGENTS.md`` missing."""
    tmpl = setup_repo_template_path()
    if tmpl is None:
        return
    dest = root / SETUP_REPO_FILENAME
    if not dest.exists():
        try:
            shutil.copy2(tmpl, dest)
            created.append(str(dest))
        except OSError as exc:
            logger.warning("setup_repo.md copy to %s failed: %s", root, exc)
    if not dest.is_file():
        return
    if (root / AGENTS_MD_FILENAME).is_file():
        return
    notes = root / NOTES_FILENAME
    if not notes.is_file():
        return
    try:
        body = notes.read_text(encoding="utf-8")
    except OSError:
        return
    if _AGENT_BOOTSTRAP_SENTINEL in body:
        return
    block = (
        f"{_AGENT_BOOTSTRAP_SENTINEL}\n\n"
        "## Agent: run full `setup_repo.md` bootstrap\n\n"
        "This repository root has no `AGENTS.md` yet. Read **`setup_repo.md`** in this directory "
        "from start to finish and follow every step to create the agent continuity layout (mirrored "
        "rules, `project_*.md`, `repo_map.md`, etc.). Do this before major implementation so the "
        "repository matches the Hermes continuity standard.\n\n"
    )
    new_body = body.rstrip() + "\n\n" + block
    tmp = notes.parent / (notes.name + ".tmp")
    try:
        tmp.write_text(new_body, encoding="utf-8")
        tmp.replace(notes)
    except OSError as exc:
        logger.warning("notes.md bootstrap reminder append failed for %s: %s", root, exc)


def _write_text_atomic(path: Path, content: str) -> None:
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _read_text_if_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _project_policy_template(root: Path) -> str:
    for name in (AGENTS_MD_FILENAME, CLAUDE_MD_FILENAME, CURSOR_RULES_FILENAME):
        text = _read_text_if_file(root / name)
        if text and text.strip():
            return _ensure_compact_memory_policy(text)
    env_raw = (os.environ.get(HERMES_CHAT_POLICY_TEMPLATE_ENV) or "").strip()
    if env_raw:
        try:
            text = _read_text_if_file(Path(env_raw).expanduser().resolve())
        except OSError:
            text = None
        if text and text.strip():
            return _ensure_compact_memory_policy(text)
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        text = _read_text_if_file(parent / AGENTS_MD_FILENAME)
        if text and text.strip():
            return _ensure_compact_memory_policy(text)
    return _ensure_compact_memory_policy(_DEFAULT_POLICY_TEMPLATE)


def _ensure_compact_memory_policy(text: str) -> str:
    src = text or ""
    if _COMPACT_MEMORY_POLICY_SENTINEL in src:
        return src
    block = (
        "\n\n"
        f"{_COMPACT_MEMORY_POLICY_SENTINEL}\n"
        "Compact project memory workflow:\n"
        "- Read `project_memory/index.json` first for token-light navigation.\n"
        "- Use `repo_map.md` as human-readable backup, not the primary full context payload.\n"
        "- Do not load full `project_history.md` by default; only recent tail entries when needed.\n"
        "- Keep `project_memory/index.json` current after structural changes.\n"
    )
    return src.rstrip() + block + "\n"


def _sync_project_policy_files(
    root: Path,
    *,
    created: list[str],
    updated: list[str],
) -> None:
    template = _project_policy_template(root)
    for name in (AGENTS_MD_FILENAME, CLAUDE_MD_FILENAME, CURSOR_RULES_FILENAME):
        dest = root / name
        current = _read_text_if_file(dest)
        if current is None:
            _write_text_atomic(dest, template)
            created.append(str(dest))
            continue
        if current != template:
            _write_text_atomic(dest, template)
            updated.append(str(dest))


def ensure_workspace_files(
    root: Path,
    *,
    generate_repo_map_if_missing: bool = True,
) -> dict[str, Any]:
    """Create standard workspace markdown files when missing."""
    root = normalize_project_root(root)
    created: list[str] = []
    updated: list[str] = []
    hist = root / HISTORY_FILENAME
    if not hist.exists():
        hist.write_text(HISTORY_HEADER, encoding="utf-8")
        created.append(str(hist))
    repo = root / REPO_MAP_FILENAME
    if not repo.exists() and generate_repo_map_if_missing:
        refresh_repo_map(root, ensure_workspace=False)
        created.append(str(repo))
    notes = root / NOTES_FILENAME
    if not notes.exists():
        notes.write_text(NOTES_HEADER, encoding="utf-8")
        created.append(str(notes))
    goal = root / GOAL_FILENAME
    if not goal.exists():
        goal.write_text(GOAL_HEADER, encoding="utf-8")
        created.append(str(goal))
    status = root / STATUS_FILENAME
    if not status.exists():
        status.write_text(STATUS_HEADER, encoding="utf-8")
        created.append(str(status))
    knowledge = root / KNOWLEDGE_FILENAME
    if not knowledge.exists():
        knowledge.write_text(KNOWLEDGE_HEADER, encoding="utf-8")
        created.append(str(knowledge))
    mem_dir = root / PROJECT_MEMORY_DIRNAME
    if not mem_dir.exists():
        mem_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(mem_dir))
    memory_index = mem_dir / PROJECT_MEMORY_INDEX_FILENAME
    if not memory_index.exists():
        info = refresh_project_memory_index(root)
        created.append(str(memory_index))
        if info.get("entries", 0) == 0:
            logger.debug("project memory index created empty for %s", root)
    elif _project_memory_index_needs_refresh(memory_index):
        refresh_project_memory_index(root)
        updated.append(str(memory_index))
    _sync_project_policy_files(root, created=created, updated=updated)
    _maybe_install_setup_repo_and_agent_bootstrap_note(root, created)
    return {"path": str(root), "created": created, "updated": updated}


def read_workspace_file(root: Path, name: str, *, ensure: bool = False) -> str:
    root = normalize_project_root(root)
    if ensure:
        ensure_workspace_files(root, generate_repo_map_if_missing=True)
    if name == "project_history":
        fn = HISTORY_FILENAME
    elif name == "repo_map":
        fn = REPO_MAP_FILENAME
    elif name == "notes":
        fn = NOTES_FILENAME
    elif name == "project_goal":
        fn = GOAL_FILENAME
    elif name == "project_status":
        fn = STATUS_FILENAME
    elif name == "project_knowledge":
        fn = KNOWLEDGE_FILENAME
    else:
        raise ValueError(
            "name must be project_history, repo_map, notes, project_goal, "
            "project_status, or project_knowledge"
        )
    path = root / fn
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_workspace_file(root: Path, name: str, content: str) -> None:
    root = normalize_project_root(root)
    if name == "project_history":
        fn = HISTORY_FILENAME
    elif name == "repo_map":
        fn = REPO_MAP_FILENAME
    elif name == "notes":
        fn = NOTES_FILENAME
    elif name == "project_goal":
        fn = GOAL_FILENAME
    elif name == "project_status":
        fn = STATUS_FILENAME
    elif name == "project_knowledge":
        fn = KNOWLEDGE_FILENAME
    else:
        raise ValueError(
            "name must be project_history, repo_map, notes, project_goal, "
            "project_status, or project_knowledge"
        )
    if not isinstance(content, str):
        raise TypeError("content must be str")
    path = root / fn
    _write_text_atomic(path, content)
