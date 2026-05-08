from __future__ import annotations

import io
import json
import logging
import os
from dataclasses import dataclass
from statistics import mean
from typing import Any

import httpx

from animus.beta.context_protocol.request_adapter import apply_beta_context_protocol


@dataclass
class PromptCase:
    name: str
    prompt: str
    expected_tools: set[str]
    expected_skills: set[str]
    code_only: bool = True


PROMPT_CASES: list[PromptCase] = [
    PromptCase(
        name="Locate API handler and summarize flow",
        prompt="Find where /api/chat is handled, read the relevant files, and summarize the request flow.",
        expected_tools={"search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Code fix with patch",
        prompt="Search for timeout handling in API server, edit code to fix it, and apply a patch.",
        expected_tools={"search_files", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Run tests",
        prompt="Run targeted unit tests for api_server and report failures.",
        expected_tools={"terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Browser UI verification",
        prompt="Navigate to the web app, take a snapshot, click login, and verify form behavior.",
        expected_tools={"browser_navigate", "browser_snapshot", "browser_click"},
        expected_skills=set(),
        code_only=False,
    ),
    PromptCase(
        name="Security vulnerability scan",
        prompt="Audit authentication and token validation paths for vulnerabilities and unsafe assumptions.",
        expected_tools={"search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Security review",
        prompt="Review auth middleware for security risks and list possible regressions.",
        expected_tools={"search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Cross-file refactor",
        prompt="Refactor duplicated helper logic across files and patch all call sites.",
        expected_tools={"search_files", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Intermittent integration failure",
        prompt="Debug intermittent integration test failures by checking process state and reading failing fixture files.",
        expected_tools={"process", "read_file", "search_files"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Flaky test debugging",
        prompt="Investigate a flaky gateway test, run it repeatedly, inspect logs, and identify root cause.",
        expected_tools={"terminal", "process", "search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Skill system diagnostics",
        prompt="Inspect the skill system workflow and list available skills before proposing changes.",
        expected_tools={"skills_list"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Skill creation workflow",
        prompt="Create a reusable skill for release checklist automation and validate it.",
        expected_tools={"skill_manage", "skills_list"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Session history lookup",
        prompt="Search prior sessions for similar model timeout errors and compare mitigation steps.",
        expected_tools={"session_search"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Todo-driven implementation",
        prompt="Break the fix into todos, implement each step, and update todo statuses as you go.",
        expected_tools={"todo", "search_files", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Web research + local edit",
        prompt="Use browser navigation to inspect docs behavior, then update local code and patch docs.",
        expected_tools={"browser_navigate", "read_file", "patch"},
        expected_skills=set(),
        code_only=False,
    ),
    PromptCase(
        name="Code edit with tests",
        prompt="Find the API validation bug, patch the handler, and run focused tests.",
        expected_tools={"search_files", "read_file", "patch", "terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Repo search only",
        prompt="Locate all references to context protocol diagnostics and report file locations.",
        expected_tools={"search_files"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Read and summarize file",
        prompt="Open the beta context protocol config file and summarize active-mode gates.",
        expected_tools={"read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Test failure triage",
        prompt="Investigate a test failure report, read failing test files, and identify likely root causes.",
        expected_tools={"terminal", "search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Debugging with process context",
        prompt="Debug a stuck local run by checking active processes and then reading relevant source files.",
        expected_tools={"process", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Security regression check",
        prompt="Review the recent auth patch for security regressions and scan adjacent code paths.",
        expected_tools={"search_files", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Skill workflow hardening",
        prompt="Create skill workflow checks and verify skill system coverage for release automation.",
        expected_tools={"skills_list", "skill_manage"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Multi-step implementation plan",
        prompt="Search the repo, read implementation files, create a todo list, patch code, and run tests.",
        expected_tools={"search_files", "read_file", "todo", "patch", "terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Data lookup task",
        prompt="Look up the latest API pricing data and summarize impact on routing defaults.",
        expected_tools={"web_search"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Refactor and verify",
        prompt="Refactor duplicated timeout helpers, patch call sites, then execute impacted tests.",
        expected_tools={"search_files", "read_file", "patch", "terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Failure isolation analysis",
        prompt="Trace failing test behavior, inspect process state, and isolate whether failures are infra or logic.",
        expected_tools={"terminal", "process", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Skill inventory and update",
        prompt="List installed skills, review the release-checklist skill content, and update it if needed.",
        expected_tools={"skills_list", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Cross-module bug hunt",
        prompt="Find bug sources across modules, inspect files, and apply the minimal patch.",
        expected_tools={"search_files", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Testing workflow automation",
        prompt="Create a task checklist, run flaky tests repeatedly, and document reproducible failure conditions.",
        expected_tools={"todo", "terminal", "process", "read_file"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Security + flaky composite",
        prompt="Audit flaky auth tests for security-sensitive race conditions and inspect related files.",
        expected_tools={"search_files", "read_file", "process", "terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Skill system migration prep",
        prompt="Prepare a skill system migration plan: list skills, inspect existing workflow files, and patch docs.",
        expected_tools={"skills_list", "read_file", "patch"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Repository debugging pass",
        prompt="Debug failing gateway behavior by searching handlers, reading code, and running targeted tests.",
        expected_tools={"search_files", "read_file", "terminal"},
        expected_skills=set(),
    ),
    PromptCase(
        name="Code + browser mixed validation",
        prompt="Inspect web login behavior in browser tools, then patch local auth copy based on findings.",
        expected_tools={"browser_navigate", "browser_snapshot", "read_file", "patch"},
        expected_skills=set(),
        code_only=False,
    ),
    PromptCase(
        name="Subagent delegation",
        prompt="Delegate broad codebase exploration to a subagent and consolidate findings.",
        expected_tools={"delegate_task"},
        expected_skills=set(),
    ),
]


def _f1(precision: float, recall: float) -> float:
    if precision <= 0.0 or recall <= 0.0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def _extract_payload(raw_line: str) -> dict[str, Any]:
    if "beta_context_protocol " not in str(raw_line):
        return {}
    try:
        return json.loads(str(raw_line).split("beta_context_protocol ", 1)[1])
    except Exception:
        return {}


def _classify_failure_type(err: str) -> str:
    low = str(err or "").strip().lower()
    if any(k in low for k in ("timed out", "timeout", "read timeout")):
        return "timeout"
    return "logic"


def _build_shadow_beta_cfg() -> dict[str, Any]:
    return {
        "skill_tool_context_protocol_enabled": True,
        "skill_tool_context_protocol_mode": "shadow",
        "auto_model_router_enabled": False,
        "router_model_mode": "cheapest_enabled",
        "router_provider": None,
        "router_model": None,
        "fallback_to_manual": True,
        "selector_confidence_threshold": 0.65,
        "max_selected_tools": 8,
        "max_selected_skills": 8,
        "log_full_prompts": False,
    }


def _build_active_beta_cfg() -> dict[str, Any]:
    return {
        "skill_tool_context_protocol_enabled": True,
        "skill_tool_context_protocol_mode": "active",
        "auto_model_router_enabled": False,
        "router_model_mode": "cheapest_enabled",
        "router_provider": None,
        "router_model": None,
        "fallback_to_manual": True,
        "shadow_benchmark_passed": True,
        "decision_diagnostics_enabled": True,
        "active_local_dev_only": False,
        "selector_confidence_threshold": 0.65,
        "max_selected_tools": 8,
        "max_selected_skills": 8,
        "log_full_prompts": False,
    }


def _evaluate_prompt_case(case: PromptCase, beta_cfg: dict[str, Any], stream: io.StringIO) -> dict[str, Any]:
    stream.seek(0)
    stream.truncate(0)
    apply_beta_context_protocol(
        prompt=case.prompt,
        beta_cfg=beta_cfg,
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    raw = stream.getvalue().strip().split("\n")[-1] if stream.getvalue().strip() else ""
    payload = _extract_payload(raw)
    selected_tools = set(payload.get("selected_tools") or [])
    baseline_required = set(payload.get("baseline_required_tools") or [])
    llm_added_tools = set(payload.get("llm_added_tools") or [])
    pruned_optional_tools = set(payload.get("pruned_optional_tools") or [])
    expected_tools = set(case.expected_tools)

    hit = len(expected_tools & selected_tools)
    missed_expected = sorted(expected_tools - selected_tools)
    recall = (hit / len(expected_tools)) if expected_tools else 1.0
    precision = (hit / len(selected_tools)) if selected_tools else (1.0 if not expected_tools else 0.0)
    f1 = _f1(precision, recall)
    browser_fp = case.code_only and any(t.startswith("browser_") for t in selected_tools)
    baseline_hits = sorted(expected_tools & baseline_required)
    critical_miss = bool(missed_expected)
    return {
        "name": case.name,
        "expected_tools": sorted(expected_tools),
        "selected_tools": sorted(selected_tools),
        "baseline_required_tools": sorted(baseline_required),
        "baseline_tool_hits": baseline_hits,
        "llm_added_tools": sorted(llm_added_tools),
        "pruned_optional_tools": sorted(pruned_optional_tools),
        "missed_expected_tools": missed_expected,
        "critical_miss": critical_miss,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "browser_false_positive": browser_fp,
        "selected_tool_count": len(selected_tools),
        "fallback_used": bool(payload.get("fallback_used")),
        "estimated_tokens_saved": float(payload.get("estimated_tokens_saved") or 0.0),
    }


def _post_chat_json(
    *,
    base_url: str,
    payload: dict[str, Any],
    timeout: int,
    api_key: str | None,
) -> tuple[int, str]:
    endpoint = str(base_url or "").strip()
    if not endpoint:
        raise RuntimeError("missing base_url")
    is_animus_chat = endpoint.endswith("/api/chat")
    headers = {"Content-Type": "application/json"}
    if api_key and not is_animus_chat:
        headers["Authorization"] = f"Bearer {api_key}"
    body = dict(payload)
    if is_animus_chat:
        body["stream"] = True
    with httpx.Client(timeout=float(timeout)) as cli:
        if is_animus_chat:
            rsp = cli.post(endpoint, headers=headers, json=body)
        else:
            rsp = cli.post(f"{endpoint.rstrip('/')}/v1/chat/completions", headers=headers, json=body)
    return rsp.status_code, rsp.text


def _extract_assistant_text_from_sse(raw_text: str) -> str:
    out: list[str] = []
    for line in str(raw_text or "").splitlines():
        ln = line.strip()
        if not ln.startswith("data:"):
            continue
        data = ln[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            payload = json.loads(data)
        except Exception:
            continue
        choices = payload.get("choices") or []
        if not choices:
            continue
        delta = (choices[0] or {}).get("delta") or {}
        chunk = delta.get("content")
        if isinstance(chunk, str) and chunk:
            out.append(chunk)
    return "".join(out).strip()


def chat_once(
    *,
    base_url: str,
    prompt: str,
    beta_cfg: dict[str, Any],
    model: str,
    retries: int = 2,
    timeout: int = 300,
    api_key: str | None = None,
) -> tuple[str, str | None]:
    request_body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "hermes_beta": beta_cfg,
    }
    for i in range(retries + 1):
        try:
            status, raw_text = _post_chat_json(
                base_url=base_url,
                payload=request_body,
                timeout=timeout,
                api_key=api_key,
            )
            if status >= 400:
                raise RuntimeError(f"HTTP {status}: {raw_text[:500]}")
            if str(base_url or "").strip().endswith("/api/chat"):
                content = _extract_assistant_text_from_sse(raw_text)
            else:
                data = json.loads(raw_text) if raw_text.strip() else {}
                choices = data.get("choices") or []
                content = ""
                if choices and isinstance(choices[0], dict):
                    content = str(((choices[0].get("message") or {}).get("content") or "")).strip()
            return content, None
        except Exception as exc:
            if i == retries:
                return "", str(exc)
    return "", "unexpected retry loop termination"


def _preflight_chat_status(
    *,
    base_url: str,
    model: str,
    beta_cfg: dict[str, Any],
    api_key: str | None,
    timeout: int,
) -> tuple[int | None, int | None]:
    preflight_timeout = max(30, int(timeout))
    normal_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "stream": False,
    }
    beta_payload = dict(normal_payload)
    beta_payload["hermes_beta"] = beta_cfg
    try:
        normal_status, _ = _post_chat_json(
            base_url=base_url,
            payload=normal_payload,
            timeout=preflight_timeout,
            api_key=api_key,
        )
    except Exception:
        normal_status = None
    try:
        beta_status, _ = _post_chat_json(
            base_url=base_url,
            payload=beta_payload,
            timeout=preflight_timeout,
            api_key=api_key,
        )
    except Exception:
        beta_status = None
    return normal_status, beta_status


def run_shadow_selector_benchmark() -> dict:
    beta_cfg = _build_shadow_beta_cfg()

    logger = logging.getLogger("animus.beta.context_protocol")
    logger.setLevel(logging.INFO)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    rows: list[dict] = []
    for case in PROMPT_CASES:
        rows.append(_evaluate_prompt_case(case=case, beta_cfg=beta_cfg, stream=stream))

    logger.removeHandler(handler)

    code_only_rows = [r for r in rows if any(c.name == r["name"] and c.code_only for c in PROMPT_CASES)]
    browser_fp_rate = (
        sum(1 for r in code_only_rows if r["browser_false_positive"]) / float(len(code_only_rows))
        if code_only_rows
        else 0.0
    )
    metrics = {
        "prompt_count": len(rows),
        "avg_precision": mean(r["precision"] for r in rows),
        "avg_recall": mean(r["recall"] for r in rows),
        "avg_f1": mean(r["f1"] for r in rows),
        "browser_false_positive_rate": browser_fp_rate,
        "avg_selected_tools": mean(r["selected_tool_count"] for r in rows),
        "avg_baseline_hits": mean(len(r["baseline_tool_hits"]) for r in rows),
        "empty_selection_rate": (
            sum(1 for r in rows if r["selected_tool_count"] == 0) / float(len(rows)) if rows else 0.0
        ),
        "fallback_count": sum(1 for r in rows if r["fallback_used"]),
        "critical_miss_count": sum(1 for r in rows if r["critical_miss"]),
        "rows": rows,
    }
    return metrics


def run_active_trial_extended(
    *,
    retries: int = 2,
    timeout: int = 300,
    prompts: list[PromptCase] | None = None,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    active_cfg = _build_active_beta_cfg()
    eval_prompts = list(prompts or PROMPT_CASES)
    gateway_url = str(
        base_url
        or os.getenv("ANIMUS_CHAT_URL")
        or os.getenv("HERMES_API_URL")
        or "http://127.0.0.1:8642"
    ).strip()
    eval_model = str(model or os.getenv("ANIMUS_BETA_TRIAL_MODEL") or "gpt-4.1-mini").strip()
    bearer = api_key or os.getenv("HERMES_API_KEY")
    preflight_normal_status, preflight_beta_status = _preflight_chat_status(
        base_url=gateway_url,
        model=eval_model,
        beta_cfg=active_cfg,
        api_key=bearer,
        timeout=timeout,
    )

    logger = logging.getLogger("animus.beta.context_protocol")
    logger.setLevel(logging.INFO)
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    rows: list[dict[str, Any]] = []
    timeout_failures = 0
    logic_failures = 0
    quality_regressions = 0
    critical_miss_count = 0

    for case in eval_prompts:
        # Temporary guardrail inputs: once any critical miss or logic failure occurs,
        # request_adapter should force active mode down to shadow for subsequent prompts.
        active_cfg["critical_miss_count"] = critical_miss_count
        active_cfg["logic_failures"] = logic_failures
        row = _evaluate_prompt_case(case=case, beta_cfg=active_cfg, stream=stream)
        if row["critical_miss"]:
            critical_miss_count += 1

        response_text, err = chat_once(
            base_url=gateway_url,
            prompt=case.prompt,
            beta_cfg=active_cfg,
            model=eval_model,
            retries=retries,
            timeout=timeout,
            api_key=bearer,
        )
        failure_type = ""
        if err:
            failure_type = _classify_failure_type(err)
            if failure_type == "timeout":
                timeout_failures += 1
            else:
                logic_failures += 1
        elif not str(response_text or "").strip():
            quality_regressions += 1
            err = "empty assistant response"
            failure_type = "logic"
            logic_failures += 1

        row["chat_error"] = err
        row["failure_type"] = failure_type
        row["chat_ok"] = err is None
        rows.append(row)

    logger.removeHandler(handler)

    avg_token_savings = mean(r.get("estimated_tokens_saved", 0.0) for r in rows) if rows else 0.0
    task_failures = sum(1 for r in rows if not r["chat_ok"])
    metrics: dict[str, Any] = {
        "prompts_run": len(rows),
        "normal_call_status": preflight_normal_status,
        "beta_call_status": preflight_beta_status,
        "fallback_count": sum(1 for r in rows if r["fallback_used"]),
        "critical_miss_count": critical_miss_count,
        "timeout_failures": timeout_failures,
        "logic_failures": logic_failures,
        "task_failures": task_failures,
        "quality_regressions": quality_regressions,
        "avg_token_savings": avg_token_savings,
        "rows": rows,
    }
    return metrics


def active_mode_gate(metrics: dict) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if metrics["avg_recall"] < 0.70:
        failures.append("recall < 0.70")
    if metrics["avg_precision"] < 0.50:
        failures.append("precision < 0.50")
    if metrics["browser_false_positive_rate"] > 0.05:
        failures.append("browser false-positive rate too high")
    if metrics["avg_selected_tools"] > 4.0:
        failures.append("avg selected tools > 4")
    return (len(failures) == 0, failures)

