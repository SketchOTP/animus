from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from animus.plugins.command_brief.constants import APPROVED_GOVERNANCE_RELATIVE, INFERENCE_RECENT_DAYS


def _iso_mtime(ts: float | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, ValueError, OverflowError):
        return None


@dataclass(frozen=True)
class GovernanceBundle:
    """Approved-doc snapshot for one workspace root (read-only, bounded)."""

    workspace: Path
    texts: dict[str, str]
    mtimes_iso: dict[str, str | None]
    max_mtime_epoch: float | None
    errors: list[str]


def read_governance_stats(workspace: Path) -> GovernanceBundle:
    """Stat-only scan of approved paths (no file body reads)."""
    mtimes: dict[str, str | None] = {}
    errors: list[str] = []
    max_epoch: float | None = None
    root = workspace
    for rel in APPROVED_GOVERNANCE_RELATIVE:
        p = root / rel
        key = rel.replace("\\", "/")
        try:
            if not p.is_file():
                mtimes[key] = None
                continue
            st = p.stat()
            mt = st.st_mtime
            max_epoch = mt if max_epoch is None else max(max_epoch, mt)
            mtimes[key] = _iso_mtime(mt)
        except OSError as exc:
            errors.append(f"{key}: {exc}")
            mtimes[key] = None
    return GovernanceBundle(
        workspace=root,
        texts={},
        mtimes_iso=mtimes,
        max_mtime_epoch=max_epoch,
        errors=errors,
    )


def read_governance_bundle(workspace: Path, *, history_tail_lines: int = 120) -> GovernanceBundle:
    """Read only approved governance files under ``workspace`` (no directory walks)."""
    texts: dict[str, str] = {}
    mtimes: dict[str, str | None] = {}
    errors: list[str] = []
    max_epoch: float | None = None
    root = workspace
    for rel in APPROVED_GOVERNANCE_RELATIVE:
        p = root / rel
        key = rel.replace("\\", "/")
        try:
            if not p.is_file():
                mtimes[key] = None
                continue
            st = p.stat()
            mt = st.st_mtime
            max_epoch = mt if max_epoch is None else max(max_epoch, mt)
            mtimes[key] = _iso_mtime(mt)
            raw = p.read_text(encoding="utf-8", errors="replace")
            if rel == "project_history.md":
                lines = raw.splitlines()
                if len(lines) > history_tail_lines:
                    raw = "\n".join(lines[-history_tail_lines:])
            texts[key] = raw
        except OSError as exc:
            errors.append(f"{key}: {exc}")
            mtimes[key] = None
    return GovernanceBundle(
        workspace=root,
        texts=texts,
        mtimes_iso=mtimes,
        max_mtime_epoch=max_epoch,
        errors=errors,
    )


def governance_digest_for_prompt(bundle: GovernanceBundle) -> str:
    parts: list[str] = []
    for rel in APPROVED_GOVERNANCE_RELATIVE:
        key = rel.replace("\\", "/")
        if key not in bundle.texts:
            continue
        parts.append(f"### FILE: {key}\n{bundle.texts[key]}\n")
    return "\n".join(parts).strip()


def parse_generated_at_iso(iso: str | None) -> float | None:
    if not iso or not isinstance(iso, str):
        return None
    t = iso.strip()
    if not t:
        return None
    try:
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        return datetime.fromisoformat(t).timestamp()
    except ValueError:
        return None


def docs_changed_since(
    bundle: GovernanceBundle,
    generated_at_iso: str | None,
) -> bool:
    """True if any present approved file is newer than ``generated_at`` (or no cache time)."""
    gen_ts = parse_generated_at_iso(generated_at_iso)
    if gen_ts is None:
        return bundle.max_mtime_epoch is not None
    if bundle.max_mtime_epoch is None:
        return False
    return bundle.max_mtime_epoch > gen_ts + 0.5


def modified_within_recent_window(max_mtime_epoch: float | None, recent_days: int, now: float | None = None) -> bool:
    if max_mtime_epoch is None:
        return False
    if now is None:
        now = datetime.now(tz=timezone.utc).timestamp()
    span = float(recent_days) * 86400.0
    return (now - max_mtime_epoch) <= span


def governance_fresh_for_command_brief_inference(stats: GovernanceBundle) -> bool:
    """Hard gate for any summarizer call: max approved-doc mtime within ``INFERENCE_RECENT_DAYS``."""
    return modified_within_recent_window(stats.max_mtime_epoch, INFERENCE_RECENT_DAYS, None)
