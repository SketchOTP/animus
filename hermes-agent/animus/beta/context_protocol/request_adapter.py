from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from typing import Any

from agent.auxiliary_client import call_llm

from .beta_config import normalize_beta_context_protocol_config
from .fallback import fallback
from .guards import validate_router_decision, validate_selector_decision
from .logging import estimate_context_tokens, log_decision, now_iso, prompt_hash
from .registry_snapshot import build_registry_snapshot
from .router import choose_router_target, run_router
from .schema import BetaDecisionLog, BetaMode, ComplexityLevel, RouterDecision, SelectorDecision
from .selector import run_selector

logger = logging.getLogger("animus.beta.context_protocol")
_BROWSER_INTENT_TERMS = (
    "browser",
    "webpage",
    "website",
    "dom",
    "screenshot",
    "click",
    "navigate",
    "inspect page",
    "ui test",
    "playwright",
    "selenium",
)
_CODE_INTENT_TERMS = (
    "refactor",
    "fix",
    "test",
    "code",
    "function",
    "debug",
    "bug",
    "implement",
)
_FILE_INTENT_TERMS = ("file", "edit", "update", "write", "patch", "modify")
_SEARCH_INTENT_TERMS = ("search", "find", "locate", "where", "grep")
_API_DATA_INTENT_TERMS = ("api", "latest", "data", "lookup")
_TASKLIST_INTENT_TERMS = ("todo", "task", "tasks", "checklist", "worklist", "backlog")


@dataclass
class BetaAdapterResult:
    mode: BetaMode
    selected_tools: list[str]
    selected_skills: list[str]
    selected_provider: str | None
    selected_model: str | None
    fallback_used: bool
    fallback_reason: str | None


def _mode_from_raw(raw: str) -> BetaMode:
    v = str(raw or "").strip().lower()
    if v == "shadow":
        return BetaMode.SHADOW
    if v == "active":
        return BetaMode.ACTIVE
    return BetaMode.OFF


def _decision_model_for_request(
    *,
    candidates: list[dict],
    router_model_mode: str,
    router_provider: str | None,
    router_model: str | None,
) -> tuple[str | None, str | None]:
    provider, model, _ = choose_router_target(
        candidates=candidates,
        router_model_mode=router_model_mode,
        router_provider=router_provider,
        router_model=router_model,
    )
    return provider, model


def _strip_json_fence(raw: str) -> str:
    txt = str(raw or "").strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if "\n" in txt:
            txt = txt.split("\n", 1)[1]
    if txt.endswith("```"):
        txt = txt[:-3].strip()
    return txt


def _parse_json_obj(raw: str) -> dict[str, Any]:
    text = _strip_json_fence(raw)
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("decision payload is not an object")
    return obj


def _coerce_complexity(raw: Any) -> ComplexityLevel:
    try:
        return ComplexityLevel(str(raw or "").strip().lower())
    except Exception:
        return ComplexityLevel.MEDIUM


def _coerce_selector_decision(obj: dict[str, Any]) -> SelectorDecision:
    tool_items: list[tuple[str, float, str]] = []
    for raw in (obj.get("selected_tools") or []):
        if isinstance(raw, dict):
            tool_id = str(raw.get("id") or "").strip()
            if not tool_id:
                continue
            try:
                relevance = float(raw.get("relevance", 0.0))
            except (TypeError, ValueError):
                relevance = 0.0
            reason = str(raw.get("reason") or "")
            tool_items.append((tool_id, relevance, reason))
        else:
            tool_id = str(raw or "").strip()
            if tool_id:
                tool_items.append((tool_id, 0.7, "Legacy selection item"))
    skill_items: list[tuple[str, float, str]] = []
    for raw in (obj.get("selected_skills") or []):
        if isinstance(raw, dict):
            skill_id = str(raw.get("id") or "").strip()
            if not skill_id:
                continue
            try:
                relevance = float(raw.get("relevance", 0.0))
            except (TypeError, ValueError):
                relevance = 0.0
            reason = str(raw.get("reason") or "")
            skill_items.append((skill_id, relevance, reason))
        else:
            skill_id = str(raw or "").strip()
            if skill_id:
                skill_items.append((skill_id, 0.7, "Legacy selection item"))
    tools = [x[0] for x in tool_items]
    skills = [x[0] for x in skill_items]
    try:
        confidence = float(obj.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return SelectorDecision(
        selected_tools=tools,
        selected_skills=skills,
        selected_tool_relevance={x[0]: float(x[1]) for x in tool_items},
        selected_skill_relevance={x[0]: float(x[1]) for x in skill_items},
        selected_tool_reasons={x[0]: x[2] for x in tool_items},
        selected_skill_reasons={x[0]: x[2] for x in skill_items},
        complexity=_coerce_complexity(obj.get("complexity")),
        confidence=confidence,
        reason=str(obj.get("reason") or ""),
    )


def _coerce_router_decision(obj: dict[str, Any]) -> RouterDecision:
    selector_view = _coerce_selector_decision(obj)
    out = RouterDecision(
        provider=str(obj.get("provider") or "").strip() or None,
        model=str(obj.get("model") or "").strip() or None,
        selected_tools=selector_view.selected_tools,
        selected_skills=selector_view.selected_skills,
        complexity=selector_view.complexity,
        confidence=selector_view.confidence,
        reason=selector_view.reason,
    )
    # Attach relevance maps for downstream deterministic pruning.
    setattr(out, "selected_tool_relevance", selector_view.selected_tool_relevance)
    setattr(out, "selected_skill_relevance", selector_view.selected_skill_relevance)
    return out


def _llm_decision_call(
    *,
    provider: str,
    model: str,
    base_url: str | None,
    api_key: str | None,
    api_mode: str | None,
    main_runtime: dict[str, Any] | None,
    prompt: str,
    snapshot: dict,
    candidates: list[dict],
    is_router: bool,
) -> dict[str, Any]:
    if is_router:
        schema_hint = (
            '{"provider":"enabled_provider","model":"enabled_model","selected_tools":[{"id":"tool_id","relevance":0.91,"reason":"why"}],'
            '"selected_skills":[{"id":"skill_id","relevance":0.81,"reason":"why"}],"complexity":"low|medium|high","confidence":0.0,"reason":"..."}'
        )
        routing_hint = json.dumps(candidates, ensure_ascii=False)
    else:
        schema_hint = (
            '{"selected_tools":[{"id":"tool_id","relevance":0.91,"reason":"why"}],'
            '"selected_skills":[{"id":"skill_id","relevance":0.81,"reason":"why"}],'
            '"complexity":"low|medium|high","confidence":0.0,"reason":"..."}'
        )
        routing_hint = "[]"
    messages = [
        {
            "role": "system",
            "content": (
                "Return strictly one JSON object only. No prose, no markdown, no code fences. "
                "Use only ids from the provided snapshot/candidates. "
                "You must include all tools strictly required to complete the task. "
                "Select only directly needed tools; prefer empty selection over weakly relevant tools. "
                "Missing a required tool is worse than including one extra tool. "
                "Do not fill slots to max; 1-3 tools is preferred unless clearly required. "
                "Do not select browser_* tools for normal code, tests, refactors, docs, repo search, or local file edits. "
                "Select browser_* tools only when prompt clearly indicates browser automation, webpage inspection, UI interaction, screenshots, DOM interaction, or live web navigation."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Task prompt:\n{prompt}\n\n"
                f"Registry snapshot JSON:\n{json.dumps(snapshot, ensure_ascii=False)}\n\n"
                f"Enabled provider/model candidates:\n{routing_hint}\n\n"
                f"Expected JSON schema shape:\n{schema_hint}\n\n"
                "Common required-tool mappings:\n"
                "- Codebase questions -> repo_search/search_files\n"
                "- File edits -> file_read/read_file and file_write/write_file/patch\n"
                "- Refactor -> repo_search/search_files + file_read/read_file\n"
                "- Tests/debugging -> repo_search/search_files + terminal/test tools\n"
                "- API/latest/data lookup -> web_search (not browser_* tools)\n\n"
                "For each selected tool include relevance in [0,1] and a short reason."
            ),
        },
    ]
    try:
        rsp = call_llm(
            provider=provider or None,
            model=model or None,
            base_url=base_url or None,
            api_key=api_key or None,
            main_runtime=main_runtime or None,
            messages=messages,
            temperature=0,
            max_tokens=1200,
            extra_body={"response_format": {"type": "json_object"}},
        )
    except Exception:
        # Some providers reject response_format=json_object; retry strict-prompt only.
        rsp = call_llm(
            provider=provider or None,
            model=model or None,
            base_url=base_url or None,
            api_key=api_key or None,
            main_runtime=main_runtime or None,
            messages=messages,
            temperature=0,
            max_tokens=1200,
        )
    _ = api_mode  # Reserved for future per-call mode tuning; runtime already carries this.
    content = str((rsp.choices[0].message.content if rsp and rsp.choices else "") or "")
    return _parse_json_obj(content)


def _coerce_runtime_hint(value: Any) -> str | None:
    txt = str(value or "").strip()
    return txt or None


def _coerce_runtime_main(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, Any] = {}
    for key in ("provider", "model", "base_url", "api_key", "api_mode", "command", "args", "credential_pool"):
        if key in raw:
            out[key] = raw.get(key)
    return out or None


def _selector_target_for_mode(
    *,
    router_enabled: bool,
    candidates: list[dict],
    router_model_mode: str,
    router_provider: str | None,
    router_model: str | None,
    current_provider: str | None,
    current_model: str | None,
) -> tuple[str | None, str | None]:
    if router_enabled:
        return _decision_model_for_request(
            candidates=candidates,
            router_model_mode=router_model_mode,
            router_provider=router_provider,
            router_model=router_model,
        )
    # Selector-only mode should follow the same active inference target as normal requests.
    if current_model:
        return current_provider, current_model
    # Backward-compatible fallback for tests/contexts that do not provide runtime hints.
    return _decision_model_for_request(
        candidates=candidates,
        router_model_mode=router_model_mode,
        router_provider=router_provider,
        router_model=router_model,
    )


def _call_selector_model(
    *,
    provider: str | None,
    model: str | None,
    runtime_base_url: str | None,
    runtime_api_key: str | None,
    runtime_api_mode: str | None,
    runtime_main: dict[str, Any] | None,
    prompt: str,
    snapshot: dict,
    candidates: list[dict],
    is_router: bool,
) -> dict[str, Any]:
    return _llm_decision_call(
        provider=provider or "",
        model=model or "",
        base_url=runtime_base_url,
        api_key=runtime_api_key,
        api_mode=runtime_api_mode,
        main_runtime=runtime_main,
        prompt=prompt,
        snapshot=snapshot,
        candidates=candidates,
        is_router=is_router,
    )


def _has_browser_intent(prompt: str) -> bool:
    pl = str(prompt or "").lower()
    return any(term in pl for term in _BROWSER_INTENT_TERMS)


def _has_any_intent(prompt: str, terms: tuple[str, ...]) -> bool:
    pl = str(prompt or "").lower()
    return any(term in pl for term in terms)


def _is_local_dev_environment() -> bool:
    markers = (
        str(os.getenv("ANIMUS_ENV") or ""),
        str(os.getenv("HERMES_ENV") or ""),
        str(os.getenv("ENV") or ""),
    )
    normalized = " ".join(markers).strip().lower()
    return any(tok in normalized for tok in ("local", "dev", "development", "test"))


def _tool_ids_from_snapshot(snapshot: dict) -> set[str]:
    return {
        str(t.get("id") or "").strip()
        for t in (snapshot.get("tools") or [])
        if str(t.get("id") or "").strip()
    }


def _resolve_tool_id(snapshot: dict, aliases: tuple[str, ...]) -> str | None:
    tool_ids = _tool_ids_from_snapshot(snapshot)
    if not tool_ids:
        return None
    lowered = {tid.lower(): tid for tid in tool_ids}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    for alias in aliases:
        for low, original in lowered.items():
            if alias in low:
                return original
    return None


def _expected_min_tools(prompt: str, complexity: ComplexityLevel) -> int:
    code_or_search = _has_any_intent(prompt, _CODE_INTENT_TERMS) or _has_any_intent(prompt, _SEARCH_INTENT_TERMS)
    file_edit = _has_any_intent(prompt, ("edit", "update", "write", "patch", "modify"))
    if complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH):
        return 2 if file_edit and code_or_search else 1
    return 1 if code_or_search else 0


def _baseline_required_tool_ids(
    *,
    prompt: str,
    snapshot: dict,
    complexity: ComplexityLevel | None = None,
) -> set[str]:
    out: set[str] = set()
    prompt_lower = str(prompt or "").lower()
    has_code = _has_any_intent(prompt, _CODE_INTENT_TERMS)
    has_file = _has_any_intent(prompt, _FILE_INTENT_TERMS)
    has_search = _has_any_intent(prompt, _SEARCH_INTENT_TERMS)
    has_api_data = _has_any_intent(prompt, _API_DATA_INTENT_TERMS)
    has_test_debug = _has_any_intent(prompt, ("test", "debug", "flaky", "failure"))
    has_tasklist = _has_any_intent(prompt, _TASKLIST_INTENT_TERMS)

    if has_code or has_search:
        tool = _resolve_tool_id(snapshot, ("repo_search", "search_files", "rg", "grep", "search"))
        if tool:
            out.add(tool)
    if has_file:
        tool = _resolve_tool_id(snapshot, ("file_read", "read_file"))
        if tool:
            out.add(tool)
    if _has_any_intent(prompt, ("edit", "update", "write", "patch", "modify", "refactor", "fix", "implement")):
        tool = _resolve_tool_id(snapshot, ("patch",))
        if not tool:
            tool = _resolve_tool_id(snapshot, ("file_write", "write_file", "edit_file"))
        if tool:
            out.add(tool)
    if has_test_debug:
        tool = _resolve_tool_id(snapshot, ("terminal", "run_tests", "pytest", "test"))
        if tool:
            out.add(tool)
    if has_api_data and not _has_browser_intent(prompt):
        tool = _resolve_tool_id(snapshot, ("web_search", "tavily_search", "web_fetch", "websearch"))
        if tool and not str(tool).startswith("browser_"):
            out.add(tool)
    if has_tasklist:
        tool = _resolve_tool_id(snapshot, ("todo", "todo_write", "todowrite"))
        if tool:
            out.add(tool)

    # Security / audit / review workflows must include repository read/search tools.
    if any(k in prompt_lower for k in ("security", "audit", "review", "vulnerability", "scan")):
        tool = _resolve_tool_id(snapshot, ("file_read", "read_file"))
        if tool:
            out.add(tool)
        tool = _resolve_tool_id(snapshot, ("repo_search", "search_files", "rg", "grep", "search"))
        if tool:
            out.add(tool)

    # Flaky test debugging requires process inspection plus file context.
    if any(k in prompt_lower for k in ("flaky", "intermittent", "failing test", "debug test", "test failure")):
        tool = _resolve_tool_id(snapshot, ("process", "process_list", "ps"))
        if tool:
            out.add(tool)
        tool = _resolve_tool_id(snapshot, ("file_read", "read_file"))
        if tool:
            out.add(tool)

    # Skill workflows need skills inventory available for deterministic coverage.
    if any(k in prompt_lower for k in ("skill", "create skill", "skill workflow", "skill system")):
        tool = _resolve_tool_id(snapshot, ("skills_list", "skill_list"))
        if tool:
            out.add(tool)

    if complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH) and not out:
        tool = _resolve_tool_id(snapshot, ("repo_search", "search_files", "rg", "search"))
        if tool:
            out.add(tool)
    return out


def _selector_tool_cap(
    *,
    prompt: str,
    complexity: ComplexityLevel,
    max_selected_tools: int,
) -> int:
    cap = 3
    if complexity == ComplexityLevel.HIGH:
        cap = 4
    if _has_browser_intent(prompt):
        cap = max(cap, 4)
    return max(1, min(max_selected_tools, cap))


def _merge_and_prune_selector_decision(
    *,
    decision: SelectorDecision,
    prompt: str,
    snapshot: dict,
    required_tools: set[str],
    max_selected_tools: int,
    max_selected_skills: int,
    relevance_threshold: float = 0.55,
) -> tuple[SelectorDecision, dict[str, list[str]]]:
    browser_intent = _has_browser_intent(prompt)
    required = set(required_tools)
    tools = list(decision.selected_tools)
    skills = list(decision.selected_skills)
    llm_selected = list(tools)
    optional_tools = [t for t in tools if t not in required]
    dropped_browser: set[str] = set()
    if not browser_intent:
        dropped_browser = {t for t in optional_tools if t.startswith("browser_")}
        optional_tools = [t for t in optional_tools if not t.startswith("browser_")]
    low_relevance_dropped = {
        t for t in optional_tools if float(decision.selected_tool_relevance.get(t, 0.7)) < relevance_threshold
    }
    optional_tools = [t for t in optional_tools if t not in low_relevance_dropped]
    skills = [s for s in skills if float(decision.selected_skill_relevance.get(s, 0.7)) >= relevance_threshold]

    expected_min = _expected_min_tools(prompt, decision.complexity)
    merged_tools: list[str] = sorted(required)
    for tool_id in optional_tools:
        if tool_id not in merged_tools:
            merged_tools.append(tool_id)

    # Minimum viable toolset: medium/high complexity should not be empty.
    if not merged_tools and decision.complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH):
        fallback_tool = _resolve_tool_id(snapshot, ("repo_search", "search_files", "rg", "search"))
        if fallback_tool:
            merged_tools.append(fallback_tool)
            required.add(fallback_tool)

    tool_cap = _selector_tool_cap(
        prompt=prompt,
        complexity=decision.complexity,
        max_selected_tools=max_selected_tools,
    )
    tool_cap = max(tool_cap, expected_min)
    required_list = [t for t in merged_tools if t in required]
    optional_sorted = sorted(
        [t for t in merged_tools if t not in required],
        key=lambda t: float(decision.selected_tool_relevance.get(t, 0.7)),
        reverse=True,
    )
    optional_allowed = max(0, tool_cap - len(required_list))
    optional_final = optional_sorted[:optional_allowed]
    capped_out = set(optional_sorted[optional_allowed:])
    tools = required_list + optional_final
    skill_cap = max(1, min(max_selected_skills, 3))
    skills = sorted(
        skills,
        key=lambda s: float(decision.selected_skill_relevance.get(s, 0.7)),
        reverse=True,
    )[:skill_cap]

    decision.selected_tools = tools
    decision.selected_skills = skills
    decision.selected_tool_relevance = {k: v for k, v in decision.selected_tool_relevance.items() if k in set(tools)}
    decision.selected_skill_relevance = {k: v for k, v in decision.selected_skill_relevance.items() if k in set(skills)}
    decision.selected_tool_reasons = {k: v for k, v in decision.selected_tool_reasons.items() if k in set(tools)}
    decision.selected_skill_reasons = {k: v for k, v in decision.selected_skill_reasons.items() if k in set(skills)}
    llm_added = sorted(t for t in tools if t not in required)
    pruned_optional = sorted((set(llm_selected) - set(required)) - set(llm_added))
    pruned_optional = sorted(set(pruned_optional) | dropped_browser | low_relevance_dropped | capped_out)
    diagnostics = {
        "baseline_required_tools": sorted(required),
        "llm_selected_tools": sorted(set(llm_selected)),
        "llm_added_tools": llm_added,
        "pruned_optional_tools": pruned_optional,
    }
    return decision, diagnostics


def apply_beta_context_protocol(
    *,
    prompt: str,
    beta_cfg: dict,
    enabled_toolsets: list[str],
    disabled_tools: list[str],
    candidates: list[dict],
) -> BetaAdapterResult:
    beta_cfg = normalize_beta_context_protocol_config(
        beta_cfg if isinstance(beta_cfg, dict) else {}
    )
    enabled = bool(beta_cfg["skill_tool_context_protocol_enabled"])
    mode = _mode_from_raw(beta_cfg["skill_tool_context_protocol_mode"])
    if not enabled or mode == BetaMode.OFF:
        return BetaAdapterResult(
            mode=BetaMode.OFF,
            selected_tools=[],
            selected_skills=[],
            selected_provider=None,
            selected_model=None,
            fallback_used=False,
            fallback_reason=None,
        )

    confidence_threshold = float(beta_cfg["selector_confidence_threshold"])
    max_selected_tools = int(beta_cfg["max_selected_tools"])
    max_selected_skills = int(beta_cfg["max_selected_skills"])
    router_enabled = bool(beta_cfg["auto_model_router_enabled"])
    router_model_mode = str(beta_cfg["router_model_mode"])
    router_provider = beta_cfg["router_provider"]
    router_model = beta_cfg["router_model"]
    fallback_to_manual = bool(beta_cfg["fallback_to_manual"])
    log_full_prompts = bool(beta_cfg["log_full_prompts"])
    shadow_benchmark_passed = bool(beta_cfg["shadow_benchmark_passed"])
    decision_diagnostics_enabled = bool(beta_cfg["decision_diagnostics_enabled"])
    active_local_dev_only = bool(beta_cfg["active_local_dev_only"])
    try:
        critical_miss_count = int(beta_cfg.get("critical_miss_count", 0) or 0)
    except (TypeError, ValueError):
        critical_miss_count = 0
    try:
        logic_failures_count = int(beta_cfg.get("logic_failures", 0) or 0)
    except (TypeError, ValueError):
        logic_failures_count = 0
    temporary_guardrail_triggered = critical_miss_count > 0 or logic_failures_count > 0
    active_gate_ok = (
        mode != BetaMode.ACTIVE
        or (
            shadow_benchmark_passed
            and fallback_to_manual
            and decision_diagnostics_enabled
            and (not active_local_dev_only or _is_local_dev_environment())
            and not temporary_guardrail_triggered
        )
    )
    if mode == BetaMode.ACTIVE and not active_gate_ok:
        # Safety gate: force shadow behavior unless active prerequisites are met.
        mode = BetaMode.SHADOW

    snapshot = build_registry_snapshot(
        enabled_toolsets=enabled_toolsets,
        disabled_tools=disabled_tools,
    )
    available_tools = snapshot.get("tools") or []
    available_skills = snapshot.get("skills") or []

    selected_tools: list[str] = []
    selected_skills: list[str] = []
    selected_provider: str | None = None
    selected_model: str | None = None
    fallback_used = False
    fallback_reason: str | None = None
    complexity = ComplexityLevel.MEDIUM
    confidence = 0.0
    decision_model_used = "heuristic/heuristic"
    baseline_required_tools = _baseline_required_tool_ids(
        prompt=prompt,
        snapshot=snapshot,
        complexity=None,
    )
    llm_selected_tools: list[str] = []
    llm_added_tools: list[str] = []
    pruned_optional_tools: list[str] = []
    runtime_provider = _coerce_runtime_hint(beta_cfg.get("_inference_provider"))
    runtime_model = _coerce_runtime_hint(beta_cfg.get("_inference_model"))
    runtime_base_url = _coerce_runtime_hint(beta_cfg.get("_inference_base_url"))
    runtime_api_key = _coerce_runtime_hint(beta_cfg.get("_inference_api_key"))
    runtime_api_mode = _coerce_runtime_hint(beta_cfg.get("_inference_api_mode"))
    runtime_main = _coerce_runtime_main(beta_cfg.get("_inference_main_runtime"))

    try:
        dec_provider, dec_model = _selector_target_for_mode(
            router_enabled=router_enabled,
            candidates=candidates,
            router_model_mode=router_model_mode,
            router_provider=router_provider,
            router_model=router_model,
            current_provider=runtime_provider,
            current_model=runtime_model,
        )
        llm_error: str | None = None
        if router_enabled:
            if dec_provider and dec_model:
                decision_model_used = f"{dec_provider}/{dec_model}"
                try:
                    router_obj = _call_selector_model(
                        provider=dec_provider,
                        model=dec_model,
                        runtime_base_url=runtime_base_url,
                        runtime_api_key=runtime_api_key,
                        runtime_api_mode=runtime_api_mode,
                        runtime_main=runtime_main,
                        prompt=prompt,
                        snapshot=snapshot,
                        candidates=candidates,
                        is_router=True,
                    )
                    router_decision = _coerce_router_decision(router_obj)
                except Exception as exc:
                    llm_error = str(exc)
                    router_decision = run_router(
                        prompt=prompt,
                        snapshot=snapshot,
                        candidates=candidates,
                        max_selected_tools=max_selected_tools,
                        max_selected_skills=max_selected_skills,
                        router_model_mode=router_model_mode,
                        router_provider=router_provider,
                        router_model=router_model,
                    )
            else:
                router_decision = run_router(
                    prompt=prompt,
                    snapshot=snapshot,
                    candidates=candidates,
                    max_selected_tools=max_selected_tools,
                    max_selected_skills=max_selected_skills,
                    router_model_mode=router_model_mode,
                    router_provider=router_provider,
                    router_model=router_model,
                )
            router_selector, router_diag = _merge_and_prune_selector_decision(
                decision=SelectorDecision(
                    selected_tools=router_decision.selected_tools,
                    selected_skills=router_decision.selected_skills,
                    selected_tool_relevance=getattr(router_decision, "selected_tool_relevance", {}),
                    selected_skill_relevance=getattr(router_decision, "selected_skill_relevance", {}),
                    complexity=router_decision.complexity,
                    confidence=router_decision.confidence,
                    reason=router_decision.reason,
                ),
                prompt=prompt,
                snapshot=snapshot,
                required_tools=baseline_required_tools,
                max_selected_tools=max_selected_tools,
                max_selected_skills=max_selected_skills,
                relevance_threshold=0.55,
            )
            llm_selected_tools = list(router_diag.get("llm_selected_tools") or [])
            llm_added_tools = list(router_diag.get("llm_added_tools") or [])
            pruned_optional_tools = list(router_diag.get("pruned_optional_tools") or [])
            router_decision.selected_tools = router_selector.selected_tools
            router_decision.selected_skills = router_selector.selected_skills
            ok, reason = validate_router_decision(
                decision=router_decision,
                snapshot=snapshot,
                candidates=candidates,
                confidence_threshold=confidence_threshold,
                max_selected_tools=max_selected_tools,
                max_selected_skills=max_selected_skills,
            )
            complexity = router_decision.complexity
            confidence = router_decision.confidence
            if not ok:
                reason = reason or llm_error
                fb = fallback(reason)
                fallback_used = fb.used
                fallback_reason = fb.reason
                if not fallback_to_manual:
                    raise ValueError(f"router decision rejected: {reason}")
            else:
                selected_provider = router_decision.provider
                selected_model = router_decision.model
                selected_tools = router_decision.selected_tools
                selected_skills = router_decision.selected_skills
        else:
            if dec_provider and dec_model:
                decision_model_used = f"{dec_provider}/{dec_model}"
                try:
                    selector_obj = _call_selector_model(
                        provider=dec_provider,
                        model=dec_model,
                        runtime_base_url=runtime_base_url,
                        runtime_api_key=runtime_api_key,
                        runtime_api_mode=runtime_api_mode,
                        runtime_main=runtime_main,
                        prompt=prompt,
                        snapshot=snapshot,
                        candidates=candidates,
                        is_router=False,
                    )
                    selector_decision = _coerce_selector_decision(selector_obj)
                except Exception as exc:
                    logger.debug("selector model call failed, using heuristic: %s", exc)
                    selector_decision = run_selector(
                        prompt=prompt,
                        snapshot=snapshot,
                        max_selected_tools=max_selected_tools,
                        max_selected_skills=max_selected_skills,
                    )
            else:
                selector_decision = run_selector(
                    prompt=prompt,
                    snapshot=snapshot,
                    max_selected_tools=max_selected_tools,
                    max_selected_skills=max_selected_skills,
                )
            selector_decision, selector_diag = _merge_and_prune_selector_decision(
                decision=selector_decision,
                prompt=prompt,
                snapshot=snapshot,
                required_tools=baseline_required_tools,
                max_selected_tools=max_selected_tools,
                max_selected_skills=max_selected_skills,
                relevance_threshold=0.55,
            )
            llm_selected_tools = list(selector_diag.get("llm_selected_tools") or [])
            llm_added_tools = list(selector_diag.get("llm_added_tools") or [])
            pruned_optional_tools = list(selector_diag.get("pruned_optional_tools") or [])
            ok, reason = validate_selector_decision(
                decision=selector_decision,
                snapshot=snapshot,
                confidence_threshold=confidence_threshold,
                max_selected_tools=max_selected_tools,
                max_selected_skills=max_selected_skills,
            )
            complexity = selector_decision.complexity
            confidence = selector_decision.confidence
            if not ok:
                fb = fallback(reason)
                fallback_used = fb.used
                fallback_reason = fb.reason
            else:
                selected_tools = selector_decision.selected_tools
                selected_skills = selector_decision.selected_skills
    except Exception as exc:
        fb = fallback(str(exc))
        fallback_used = fb.used
        fallback_reason = fb.reason

    normal_tokens = estimate_context_tokens(str(snapshot))
    beta_payload = {
        "tools": [t for t in available_tools if t.get("id") in set(selected_tools)],
        "skills": [s for s in available_skills if s.get("id") in set(selected_skills)],
    }
    beta_tokens = estimate_context_tokens(str(beta_payload))
    if not selected_tools and not selected_skills:
        beta_tokens = normal_tokens

    decision_log = BetaDecisionLog(
        timestamp=now_iso(),
        mode=mode,
        prompt_hash=prompt_hash(prompt),
        selector_model=decision_model_used,
        router_enabled=router_enabled,
        selected_provider=selected_provider,
        selected_model=selected_model,
        selected_tools=list(selected_tools),
        selected_skills=list(selected_skills),
        complexity=complexity,
        confidence=float(confidence),
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        normal_estimated_context_tokens=normal_tokens,
        beta_estimated_context_tokens=beta_tokens,
        estimated_tokens_saved=max(0, normal_tokens - beta_tokens),
        selected_tools_count=len(selected_tools),
        available_tools_count=len(available_tools),
        selected_skills_count=len(selected_skills),
        available_skills_count=len(available_skills),
        baseline_required_tools=sorted(baseline_required_tools) if decision_diagnostics_enabled else [],
        llm_selected_tools=sorted(set(llm_selected_tools)) if decision_diagnostics_enabled else [],
        llm_added_tools=sorted(set(llm_added_tools)) if decision_diagnostics_enabled else [],
        pruned_optional_tools=sorted(set(pruned_optional_tools)) if decision_diagnostics_enabled else [],
    )
    log_decision(decision_log, full_prompt=prompt, log_full_prompts=log_full_prompts)

    # Shadow mode must never alter the request.
    if mode == BetaMode.SHADOW:
        return BetaAdapterResult(
            mode=mode,
            selected_tools=[],
            selected_skills=[],
            selected_provider=None,
            selected_model=None,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

    if fallback_used:
        return BetaAdapterResult(
            mode=mode,
            selected_tools=[],
            selected_skills=[],
            selected_provider=None,
            selected_model=None,
            fallback_used=True,
            fallback_reason=fallback_reason,
        )

    return BetaAdapterResult(
        mode=mode,
        selected_tools=selected_tools,
        selected_skills=selected_skills,
        selected_provider=selected_provider,
        selected_model=selected_model,
        fallback_used=False,
        fallback_reason=None,
    )

