from __future__ import annotations

# Governance-relative paths only (no repo walk). Paths use POSIX separators under workspace root.
APPROVED_GOVERNANCE_RELATIVE: tuple[str, ...] = (
    "project_status.md",
    "project_goal.md",
    "project_history.md",
    "project_knowledge.md",
    "repo_map.md",
    ".project_intel/state.json",
    ".project_intel/active_context.json",
)

DAILY_SUMMARY_FILENAME = "project_daily_summaries.md"

# Summarizer (Hermes inference) must not run unless approved governance docs have a max mtime
# within this many days — applies to auto, one, and all modes.
INFERENCE_RECENT_DAYS = 3

NO_RECENT_WORK_FOCUS = "No recent work done"

CACHE_SCHEMA_VERSION = 1
