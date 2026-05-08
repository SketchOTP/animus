from __future__ import annotations

from .schema import ComplexityLevel, SelectionItem, SelectorDecision


_HIGH_COMPLEXITY_HINTS = {
    "architecture",
    "refactor",
    "migration",
    "multi-step",
    "complex",
    "distributed",
    "integration",
}
_MEDIUM_COMPLEXITY_HINTS = {
    "debug",
    "test",
    "review",
    "investigate",
    "analyze",
    "update",
    "implement",
}


def _tokenize(prompt: str) -> set[str]:
    out: set[str] = set()
    for raw in prompt.lower().replace("/", " ").replace("-", " ").split():
        tok = "".join(ch for ch in raw if ch.isalnum())
        if len(tok) >= 3:
            out.add(tok)
    return out


def _complexity_for_prompt(prompt: str) -> ComplexityLevel:
    toks = _tokenize(prompt)
    if len(toks) >= 35 or toks.intersection(_HIGH_COMPLEXITY_HINTS):
        return ComplexityLevel.HIGH
    if len(toks) >= 15 or toks.intersection(_MEDIUM_COMPLEXITY_HINTS):
        return ComplexityLevel.MEDIUM
    return ComplexityLevel.LOW


def _rank_items(tokens: set[str], items: list[dict], max_count: int) -> list[SelectionItem]:
    scored: list[tuple[float, SelectionItem]] = []
    for item in items:
        item_id = str(item.get("id") or "").strip()
        if not item_id:
            continue
        item_tags = {str(t).strip().lower() for t in (item.get("tags") or []) if str(t).strip()}
        text_tokens = _tokenize(str(item.get("summary") or "") + " " + item_id.replace("_", " "))
        token_space = item_tags | text_tokens
        overlap = len(tokens.intersection(token_space))
        if overlap <= 0:
            continue
        overlap_denom = max(1, min(5, len(token_space)))
        coverage = overlap / float(overlap_denom)
        relevance = min(0.99, 0.4 + (0.6 * coverage))
        score = (1.5 * relevance) + (0.02 * min(len(item_tags), 8))
        reason = "Matched prompt tokens to tool/skill tags."
        scored.append((score, SelectionItem(id=item_id, relevance=round(relevance, 3), reason=reason)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:max_count]]


def run_selector(
    *,
    prompt: str,
    snapshot: dict,
    max_selected_tools: int,
    max_selected_skills: int,
) -> SelectorDecision:
    tokens = _tokenize(prompt)
    tools = snapshot.get("tools") or []
    skills = snapshot.get("skills") or []
    selected_tool_items = _rank_items(tokens, tools, max_selected_tools)
    selected_skill_items = _rank_items(tokens, skills, max_selected_skills)
    selected_tools = [it.id for it in selected_tool_items]
    selected_skills = [it.id for it in selected_skill_items]

    complexity = _complexity_for_prompt(prompt)
    density = min(1.0, (len(selected_tools) + len(selected_skills)) / float(max_selected_tools + max_selected_skills))
    confidence = round(0.45 + (0.5 * density), 3)
    reason = "Matched prompt keywords against enabled tool/skill summaries."

    return SelectorDecision(
        selected_tools=selected_tools,
        selected_skills=selected_skills,
        selected_tool_items=selected_tool_items,
        selected_skill_items=selected_skill_items,
        selected_tool_relevance={it.id: it.relevance for it in selected_tool_items},
        selected_skill_relevance={it.id: it.relevance for it in selected_skill_items},
        selected_tool_reasons={it.id: it.reason for it in selected_tool_items},
        selected_skill_reasons={it.id: it.reason for it in selected_skill_items},
        complexity=complexity,
        confidence=confidence,
        reason=reason,
    )

