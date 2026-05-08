from __future__ import annotations

from hermes_cli.models import get_pricing_for_provider

from .schema import RouterDecision
from .selector import run_selector


def _parse_price(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _lookup_model_cost(provider: str, model: str) -> float | None:
    pricing = get_pricing_for_provider(provider) or {}
    if not pricing:
        return None
    keys = [model]
    if "/" in model:
        keys.append(model.split("/", 1)[1])
    for key in keys:
        row = pricing.get(key)
        if not isinstance(row, dict):
            continue
        prompt = _parse_price(row.get("prompt"))
        completion = _parse_price(row.get("completion"))
        if prompt is None and completion is None:
            continue
        return float((prompt or 0.0) + (completion or 0.0))
    return None


def _candidate_sort_key(item: dict) -> tuple[int, int, str]:
    model = str(item.get("model") or "").lower()
    provider = str(item.get("provider") or "").lower()
    priced_cost = _lookup_model_cost(provider, model)
    cheap_marker = 0
    for kw in ("nano", "mini", "flash", "haiku", "small"):
        if kw in model:
            cheap_marker = 1
            break
    cost_sort = priced_cost if priced_cost is not None else float("inf")
    # Prefer "cheaper-looking" models first, then shorter IDs, then lexical.
    return (cost_sort, -cheap_marker, len(model), f"{provider}/{model}")


def choose_router_target(
    *,
    candidates: list[dict],
    router_model_mode: str,
    router_provider: str | None,
    router_model: str | None,
) -> tuple[str | None, str | None, str]:
    if router_model_mode == "specific_model":
        rp = (router_provider or "").strip()
        rm = (router_model or "").strip()
        if rp and rm:
            for c in candidates:
                if str(c.get("provider") or "").strip() == rp and str(c.get("model") or "").strip() == rm:
                    return rp, rm, "explicit router model"
        return None, None, "explicit router model unavailable"

    if not candidates:
        return None, None, "no enabled candidates"
    ordered = sorted(candidates, key=_candidate_sort_key)
    c0 = ordered[0]
    return str(c0.get("provider") or "").strip(), str(c0.get("model") or "").strip(), "cheapest_enabled"


def run_router(
    *,
    prompt: str,
    snapshot: dict,
    candidates: list[dict],
    max_selected_tools: int,
    max_selected_skills: int,
    router_model_mode: str,
    router_provider: str | None,
    router_model: str | None,
) -> RouterDecision:
    sel = run_selector(
        prompt=prompt,
        snapshot=snapshot,
        max_selected_tools=max_selected_tools,
        max_selected_skills=max_selected_skills,
    )
    provider, model, route_reason = choose_router_target(
        candidates=candidates,
        router_model_mode=router_model_mode,
        router_provider=router_provider,
        router_model=router_model,
    )
    confidence = sel.confidence if provider and model else 0.0
    return RouterDecision(
        provider=provider,
        model=model,
        selected_tools=sel.selected_tools,
        selected_skills=sel.selected_skills,
        complexity=sel.complexity,
        confidence=confidence,
        reason=f"{route_reason}; {sel.reason}",
    )

