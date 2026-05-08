from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from animus.plugins.command_brief.constants import DAILY_SUMMARY_FILENAME


_LOG_HEADER = """# Project Daily Summaries

This file is automatically appended by Animus Command Brief.

"""


def daily_log_path(workspace: Path) -> Path:
    return workspace / DAILY_SUMMARY_FILENAME


def read_daily_log(workspace: Path) -> str:
    p = daily_log_path(workspace)
    if not p.is_file():
        return _LOG_HEADER
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return _LOG_HEADER


def ensure_daily_log_template(workspace: Path) -> None:
    p = daily_log_path(workspace)
    if p.is_file():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_LOG_HEADER, encoding="utf-8")


def append_daily_summary(
    workspace: Path,
    *,
    model_label: str,
    status: str,
    source_files: list[str],
    current_focus: str,
    recent_changes: list[str],
    next_actions: list[str],
    risks: list[str],
) -> None:
    ensure_daily_log_template(workspace)
    p = daily_log_path(workspace)
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"## {now} - Animus Command Brief",
        "",
        f"Model: {model_label}",
        f"Status: {status}",
        "",
        "Sources:",
    ]
    for sf in source_files:
        lines.append(f"- {sf}")
    lines.extend(
        [
            "",
            "### Current Focus",
            current_focus.strip() or "(none)",
            "",
            "### Recent Changes",
        ]
    )
    if recent_changes:
        for it in recent_changes:
            lines.append(f"- {it}")
    else:
        lines.append("- (none)")
    lines.extend(["", "### Next Actions"])
    if next_actions:
        for it in next_actions:
            lines.append(f"- {it}")
    else:
        lines.append("- (none)")
    lines.extend(["", "### Risks / Blockers"])
    if risks:
        for it in risks:
            lines.append(f"- {it}")
    else:
        lines.append("- (none)")
    lines.extend(["", "---", ""])
    block = "\n".join(lines) + "\n"
    prev = p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""
    if not prev.strip():
        prev = _LOG_HEADER
    p.write_text(prev.rstrip() + "\n\n" + block, encoding="utf-8")
