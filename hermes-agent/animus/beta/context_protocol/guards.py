from __future__ import annotations

from .schema import RouterDecision, SelectorDecision


def _tool_ids(snapshot: dict) -> set[str]:
    return {
        str(t.get("id") or "").strip()
        for t in (snapshot.get("tools") or [])
        if str(t.get("id") or "").strip()
    }


def _skill_ids(snapshot: dict) -> set[str]:
    return {
        str(s.get("id") or "").strip()
        for s in (snapshot.get("skills") or [])
        if str(s.get("id") or "").strip()
    }


def validate_selector_decision(
    *,
    decision: SelectorDecision,
    snapshot: dict,
    confidence_threshold: float,
    max_selected_tools: int,
    max_selected_skills: int,
) -> tuple[bool, str | None]:
    tools = _tool_ids(snapshot)
    skills = _skill_ids(snapshot)
    if decision.confidence < confidence_threshold:
        return False, "low confidence"
    if len(decision.selected_tools) > max_selected_tools:
        return False, "selected tools exceed max"
    if len(decision.selected_skills) > max_selected_skills:
        return False, "selected skills exceed max"
    if any(t not in tools for t in decision.selected_tools):
        return False, "unknown or disabled tool selected"
    if any(s not in skills for s in decision.selected_skills):
        return False, "unknown or disabled skill selected"
    return True, None


def validate_router_decision(
    *,
    decision: RouterDecision,
    snapshot: dict,
    candidates: list[dict],
    confidence_threshold: float,
    max_selected_tools: int,
    max_selected_skills: int,
) -> tuple[bool, str | None]:
    ok, reason = validate_selector_decision(
        decision=SelectorDecision(
            selected_tools=decision.selected_tools,
            selected_skills=decision.selected_skills,
            complexity=decision.complexity,
            confidence=decision.confidence,
            reason=decision.reason,
        ),
        snapshot=snapshot,
        confidence_threshold=confidence_threshold,
        max_selected_tools=max_selected_tools,
        max_selected_skills=max_selected_skills,
    )
    if not ok:
        return ok, reason
    if not decision.provider or not decision.model:
        return False, "missing provider/model"
    enabled = {
        (str(c.get("provider") or "").strip(), str(c.get("model") or "").strip())
        for c in candidates
    }
    if (decision.provider, decision.model) not in enabled:
        return False, "router chose disabled provider/model"
    return True, None

