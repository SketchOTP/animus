from __future__ import annotations

from animus.plugins.command_brief.governance import docs_changed_since, modified_within_recent_window
from animus.plugins.command_brief.governance import GovernanceBundle


def should_regenerate_auto(
    *,
    enabled: bool,
    auto_refresh_recent: bool,
    bundle: GovernanceBundle,
    generated_at_iso: str | None,
    recent_window_days: int,
    now_ts: float | None = None,
) -> bool:
    """Auto-regeneration gate from command_brief.md pseudo-code."""
    if not enabled or not auto_refresh_recent:
        return False
    if not modified_within_recent_window(bundle.max_mtime_epoch, recent_window_days, now_ts):
        return False
    if not docs_changed_since(bundle, generated_at_iso):
        return False
    return True


def classify_display_status(
    *,
    bundle: GovernanceBundle,
    generated_at_iso: str | None,
    recent_window_days: int,
    blocked: bool,
    now_ts: float | None = None,
) -> str:
    """UI / card status when not delegating entirely to the model."""
    if blocked:
        return "blocked"
    if bundle.max_mtime_epoch is None:
        return "blocked" if bundle.errors else "unknown"
    recent = modified_within_recent_window(bundle.max_mtime_epoch, recent_window_days, now_ts)
    changed = docs_changed_since(bundle, generated_at_iso)
    if recent and changed:
        return "active"
    if changed and not recent:
        return "stale"
    if not recent:
        return "inactive"
    return "unknown"
