from __future__ import annotations

from typing import Any


def command_brief_prefs_from_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    """Normalize Command Brief settings from ``config.json`` / ``animus_ui_settings``."""
    uis = cfg.get("animus_ui_settings")
    if not isinstance(uis, dict):
        uis = {}
    raw = uis.get("commandBrief")
    if not isinstance(raw, dict):
        raw = uis.get("command_brief") if isinstance(uis.get("command_brief"), dict) else {}
    if not isinstance(raw, dict):
        raw = {}
    try:
        days = int(raw.get("recentWindowDays") if raw.get("recentWindowDays") is not None else 3)
    except (TypeError, ValueError):
        days = 3
    if days < 1:
        days = 1
    if days > 365:
        days = 365
    return {
        "enabled": bool(raw.get("enabled")),
        "autoRefreshRecent": bool(raw.get("autoRefreshRecent", True)),
        "recentWindowDays": days,
    }


def merge_command_brief_into_ui_settings(ui: dict[str, Any], prefs: dict[str, Any]) -> dict[str, Any]:
    out = dict(ui) if isinstance(ui, dict) else {}
    cb = {
        "enabled": bool(prefs.get("enabled")),
        "autoRefreshRecent": bool(prefs.get("autoRefreshRecent", True)),
        "recentWindowDays": int(prefs.get("recentWindowDays") or 3),
    }
    out["commandBrief"] = cb
    return out
