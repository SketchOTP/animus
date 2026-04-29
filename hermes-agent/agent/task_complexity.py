"""Heuristic task complexity for routing (delegation ACP, per-turn model pick)."""

from __future__ import annotations

from typing import List, Optional


def estimate_task_complexity(
    *,
    goal: Optional[str] = None,
    context: Optional[str] = None,
    toolsets: Optional[List[str]] = None,
    task_count: int = 1,
    history_message_count: int = 0,
    enabled_toolset_count: int = 0,
) -> str:
    """Return ``low``, ``medium``, or ``high`` based on text heuristics.

    ``history_message_count`` nudges toward higher complexity for long-running
    sessions (many prior turns) even when the current user message is short.
    """
    goal_text = (goal or "").strip().lower()
    context_text = (context or "").strip().lower()
    text = f"{goal_text}\n{context_text}".strip()
    words = len(text.split())

    score = 0
    if words >= 220:
        score += 2
    elif words >= 120:
        score += 1

    if history_message_count > 50:
        score += 2
    elif history_message_count > 20:
        score += 1

    high_markers = {
        "architecture",
        "orchestrate",
        "migration",
        "multi-file",
        "multi file",
        "end-to-end",
        "performance",
        "security",
        "race condition",
        "concurrency",
        "deep review",
        "comprehensive",
        "root cause",
        "full refactor",
    }
    medium_markers = {
        "debug",
        "fix",
        "tests",
        "review",
        "refactor",
        "implement",
        "integration",
    }
    low_markers = {
        "typo",
        "rename",
        "format",
        "lint",
        "small",
        "quick",
        "one-line",
    }

    for marker in high_markers:
        if marker in text:
            score += 2
    for marker in medium_markers:
        if marker in text:
            score += 1
    for marker in low_markers:
        if marker in text:
            score -= 1

    if task_count > 1:
        score += 1
    if toolsets and len(toolsets) >= 4:
        score += 1
    if enabled_toolset_count >= 6:
        score += 1

    if score >= 4:
        return "high"
    if score >= 1:
        return "medium"
    return "low"
