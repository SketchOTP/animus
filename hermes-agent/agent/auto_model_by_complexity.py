"""Pick a provider-local agentic model for this turn.

OpenAI Codex uses the live/cache Codex catalog (``get_codex_model_ids``) and a
slug-based tier ladder — not models.dev's ``openai`` slice, which does not
track Codex API slugs reliably.
Other providers use models.dev pricing metadata.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from agent.models_dev import get_model_info, list_agentic_models
from agent.task_complexity import estimate_task_complexity

logger = logging.getLogger(__name__)


def _truthy(val, default: bool = False) -> bool:
    from utils import is_truthy_value

    return is_truthy_value(val, default=default)


def _total_cost(info) -> float:
    if info is None:
        return float("inf")
    return float(info.cost_input or 0) + float(info.cost_output or 0)


def _filter_catalog_for_baseline(catalog: List[str], baseline: str) -> List[str]:
    """Prefer models under the same vendor prefix as *baseline* (aggregators)."""
    b = (baseline or "").strip()
    if "/" in b:
        prefix = b.split("/", 1)[0].lower() + "/"
        same = [m for m in catalog if m.lower().startswith(prefix)]
        if len(same) >= 2:
            return same
    return list(catalog)


def _codex_tier_rank(model_id: str) -> float:
    """Approximate capability/cost ordering for Codex slugs (lower = lighter/cheaper)."""
    m = (model_id or "").strip().lower()
    if not m:
        return 50.0
    if "max" in m:
        return 92.0
    if "nano" in m:
        return 4.0
    if "-mini" in m or ".mini" in m or m.endswith("mini"):
        return 18.0
    if "flash" in m or "lite" in m:
        return 25.0
    if "5.4-mini" in m:
        return 12.0
    if "5.4" in m and "mini" not in m:
        return 72.0
    if "5.3-codex" in m:
        return 55.0
    if "5.2-codex" in m:
        return 48.0
    if "5.1" in m and "codex" in m:
        return 40.0
    if "codex" in m:
        return 50.0
    return 50.0


def _baseline_sort_index(sorted_ids: List[str], baseline: str, provider: str) -> Optional[int]:
    """Index of *baseline* in cost-sorted *sorted_ids*, or best-effort match."""
    b = (baseline or "").strip().lower()
    if not b:
        return None
    for i, mid in enumerate(sorted_ids):
        if mid.lower() == b:
            return i
    # Normalized / bare variants
    tail = b.split("/")[-1] if "/" in b else b
    for i, mid in enumerate(sorted_ids):
        ml = mid.lower()
        if ml == tail or ml.endswith(tail) or tail.endswith(ml.split("/")[-1]):
            return i
    info = get_model_info(provider, baseline)
    if info and info.id:
        tid = info.id.lower()
        for i, mid in enumerate(sorted_ids):
            if mid.lower() == tid:
                return i
    return None


def select_model_for_turn(
    *,
    provider: str,
    baseline_model: str,
    user_message: str,
    history_message_count: int,
    enabled_toolset_count: int,
    agent_cfg: Dict,
    codex_access_token: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(model_id_or_none, complexity)``.

    When the first element is ``None``, the caller should keep *baseline_model*.
    """
    if not _truthy(agent_cfg.get("auto_model_by_complexity"), default=False):
        return None, None
    prov = (provider or "").strip().lower()
    base = (baseline_model or "").strip()
    if not prov or not base:
        return None, None

    use_codex_catalog = prov == "openai-codex"
    if use_codex_catalog:
        from hermes_cli.codex_models import get_codex_model_ids

        token = (codex_access_token or "").strip() or None
        catalog = get_codex_model_ids(access_token=token)
    else:
        catalog = list_agentic_models(prov)
    if len(catalog) < 2:
        return None, None

    candidates = _filter_catalog_for_baseline(catalog, base)
    if len(candidates) < 2:
        candidates = list(catalog)

    scored: List[tuple[float, str]] = []
    for mid in candidates:
        if use_codex_catalog:
            scored.append((_codex_tier_rank(mid), mid))
        else:
            info = get_model_info(prov, mid)
            scored.append((_total_cost(info), mid))
    scored.sort(key=lambda x: (x[0], x[1].lower()))

    sorted_ids = [m for _, m in scored]
    costs = [c for c, _ in scored]
    n = len(sorted_ids)
    if n < 2:
        return None, None

    if not use_codex_catalog:
        usable_costs = [c for c in costs if c < float("inf")]
        if len(usable_costs) < max(2, n // 4):
            # Too little pricing data — avoid wild picks; only downgrade on clear low tier.
            complexity = estimate_task_complexity(
                goal=user_message,
                context="",
                toolsets=None,
                task_count=1,
                history_message_count=history_message_count,
                enabled_toolset_count=enabled_toolset_count,
            )
            if complexity != "low":
                return None, complexity
            low_pick = None
            for pref in ("nano", "mini", "flash", "haiku", "lite"):
                for mid in sorted_ids:
                    if pref in mid.lower():
                        low_pick = mid
                        break
                if low_pick:
                    break
            if not low_pick or low_pick.lower() == base.lower():
                return None, complexity
            try:
                from hermes_cli.model_normalize import normalize_model_for_provider

                normalized = normalize_model_for_provider(low_pick, prov)
            except Exception:
                normalized = low_pick
            if normalized == base:
                return None, complexity
            return normalized, complexity

    b_idx = _baseline_sort_index(sorted_ids, base, prov)
    if b_idx is None:
        b_idx = min(n - 1, max(0, n * 3 // 4))

    complexity = estimate_task_complexity(
        goal=user_message,
        context="",
        toolsets=None,
        task_count=1,
        history_message_count=history_message_count,
        enabled_toolset_count=enabled_toolset_count,
    )

    if complexity == "high":
        pick_idx = max(b_idx, (n - 1) * 3 // 4)
    elif complexity == "medium":
        mid_idx = (n - 1) // 2
        pick_idx = min(mid_idx, b_idx)
    else:
        pick_idx = 0

    pick_idx = max(0, min(pick_idx, n - 1))
    chosen = sorted_ids[pick_idx]
    if chosen.lower() == base.lower():
        return None, complexity

    try:
        from hermes_cli.model_normalize import normalize_model_for_provider

        chosen = normalize_model_for_provider(chosen, prov)
    except Exception:
        pass

    if not chosen or chosen == base:
        return None, complexity

    logger.info(
        "auto_model_by_complexity: provider=%s complexity=%s pick=%s baseline=%s",
        prov,
        complexity,
        chosen,
        base,
    )
    return chosen, complexity
