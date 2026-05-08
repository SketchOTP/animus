"""Shared defaults and validation for the skill/tool context-protocol beta config."""

from __future__ import annotations


def default_beta_context_protocol_config() -> dict:
    return {
        "skill_tool_context_protocol_enabled": False,
        "skill_tool_context_protocol_mode": "off",
        "auto_model_router_enabled": False,
        "router_model_mode": "cheapest_enabled",
        "router_provider": None,
        "router_model": None,
        "fallback_to_manual": True,
        "shadow_benchmark_passed": False,
        "decision_diagnostics_enabled": True,
        "active_local_dev_only": True,
        "selector_confidence_threshold": 0.65,
        "max_selected_tools": 8,
        "max_selected_skills": 8,
        "log_full_prompts": False,
    }


def normalize_beta_context_protocol_config(raw: object) -> dict:
    """Return a full, validated beta config dict (ANIMUS UI, gateway body, or tests)."""
    defaults = default_beta_context_protocol_config()
    out = dict(defaults)
    if isinstance(raw, dict):
        out.update(raw)
    mode = str(out.get("skill_tool_context_protocol_mode") or "off").strip().lower()
    if mode not in {"off", "shadow", "active"}:
        mode = "off"
    out["skill_tool_context_protocol_mode"] = mode
    out["skill_tool_context_protocol_enabled"] = bool(out.get("skill_tool_context_protocol_enabled"))
    out["auto_model_router_enabled"] = bool(out.get("auto_model_router_enabled"))
    rmm = str(out.get("router_model_mode") or "cheapest_enabled").strip().lower()
    if rmm not in {"cheapest_enabled", "specific_model"}:
        rmm = "cheapest_enabled"
    out["router_model_mode"] = rmm
    rp = str(out.get("router_provider") or "").strip()
    rm = str(out.get("router_model") or "").strip()
    out["router_provider"] = rp or None
    out["router_model"] = rm or None
    out["fallback_to_manual"] = bool(out.get("fallback_to_manual"))
    out["shadow_benchmark_passed"] = bool(out.get("shadow_benchmark_passed"))
    out["decision_diagnostics_enabled"] = bool(out.get("decision_diagnostics_enabled", True))
    out["active_local_dev_only"] = bool(out.get("active_local_dev_only", True))
    try:
        thr = float(out.get("selector_confidence_threshold", 0.65))
    except (TypeError, ValueError):
        thr = 0.65
    out["selector_confidence_threshold"] = max(0.0, min(1.0, thr))
    try:
        mt = int(out.get("max_selected_tools", 8))
    except (TypeError, ValueError):
        mt = 8
    try:
        ms = int(out.get("max_selected_skills", 8))
    except (TypeError, ValueError):
        ms = 8
    out["max_selected_tools"] = max(1, mt)
    out["max_selected_skills"] = max(1, ms)
    out["log_full_prompts"] = bool(out.get("log_full_prompts"))
    return out
