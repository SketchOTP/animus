from __future__ import annotations

from animus.beta.context_protocol.beta_config import normalize_beta_context_protocol_config
from animus.beta.context_protocol.request_adapter import apply_beta_context_protocol
from animus.beta.context_protocol.router import choose_router_target


def _base_beta(**overrides):
    base = normalize_beta_context_protocol_config({})
    base.update(
        {
            "skill_tool_context_protocol_enabled": True,
            "skill_tool_context_protocol_mode": "active",
            "shadow_benchmark_passed": True,
            "active_local_dev_only": False,
        }
    )
    base.update(overrides)
    return base


def test_choose_router_target_cheapest_enabled_prefers_lower_priced_model(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.router._lookup_model_cost",
        lambda provider, model: 1.2 if model == "gpt-4o" else 0.3,
    )
    provider, model, reason = choose_router_target(
        candidates=[
            {"provider": "openai", "model": "gpt-4o"},
            {"provider": "openai", "model": "gpt-4.1-mini"},
        ],
        router_model_mode="cheapest_enabled",
        router_provider=None,
        router_model=None,
    )
    assert provider == "openai"
    assert model == "gpt-4.1-mini"
    assert reason == "cheapest_enabled"


def test_apply_beta_off_is_noop():
    result = apply_beta_context_protocol(
        prompt="test",
        beta_cfg={"skill_tool_context_protocol_enabled": False, "skill_tool_context_protocol_mode": "off"},
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[],
    )
    assert result.mode.value == "off"
    assert result.selected_tools == []
    assert result.selected_skills == []
    assert result.selected_provider is None
    assert result.selected_model is None


def test_apply_beta_shadow_never_applies_selection(monkeypatch):
    def _fake_snapshot(**kwargs):
        return {
            "tools": [{"id": "read_file", "summary": "read", "tags": ["read"]}],
            "skills": [{"id": "code_review", "summary": "review", "tags": ["review"]}],
        }

    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        _fake_snapshot,
    )

    result = apply_beta_context_protocol(
        prompt="please review this code",
        beta_cfg=_base_beta(skill_tool_context_protocol_mode="shadow"),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[],
    )
    assert result.mode.value == "shadow"
    assert result.selected_tools == []
    assert result.selected_skills == []
    assert result.selected_provider is None
    assert result.selected_model is None


def test_apply_beta_active_with_invalid_selector_falls_back(monkeypatch):
    def _fake_snapshot(**kwargs):
        return {"tools": [], "skills": []}

    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        _fake_snapshot,
    )
    result = apply_beta_context_protocol(
        prompt="do a thing",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[],
    )
    assert result.fallback_used is True
    assert result.selected_tools == []
    assert result.selected_skills == []


def test_apply_beta_router_invalid_candidate_falls_back(monkeypatch):
    def _fake_snapshot(**kwargs):
        return {
            "tools": [{"id": "read_file", "summary": "read", "tags": ["read"]}],
            "skills": [{"id": "code_review", "summary": "review", "tags": ["review"]}],
        }

    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        _fake_snapshot,
    )
    result = apply_beta_context_protocol(
        prompt="review code",
        beta_cfg=_base_beta(
            auto_model_router_enabled=True,
            router_model_mode="specific_model",
            router_provider="openai",
            router_model="gpt-4.1-mini",
        ),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "anthropic", "model": "claude-3-5-sonnet"}],
    )
    assert result.fallback_used is True
    assert result.selected_provider is None
    assert result.selected_model is None


def test_apply_beta_selector_uses_mocked_llm_response(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "read_file", "summary": "read", "tags": ["read"]}],
            "skills": [{"id": "code_review", "summary": "review", "tags": ["review"]}],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [{"id": "read_file", "relevance": 0.9, "reason": "needed"}],
            "selected_skills": ["code_review"],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "repo inspection",
        },
    )
    result = apply_beta_context_protocol(
        prompt="inspect repo",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.fallback_used is False
    assert result.selected_tools == ["read_file"]
    assert result.selected_skills == ["code_review"]


def test_apply_beta_router_uses_mocked_llm_response(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "read_file", "summary": "read", "tags": ["read"]}],
            "skills": [{"id": "code_review", "summary": "review", "tags": ["review"]}],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "selected_tools": [{"id": "read_file", "relevance": 0.91, "reason": "needed"}],
            "selected_skills": ["code_review"],
            "complexity": "medium",
            "confidence": 0.91,
            "reason": "needs code review",
        },
    )
    result = apply_beta_context_protocol(
        prompt="review code",
        beta_cfg=_base_beta(auto_model_router_enabled=True),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.fallback_used is False
    assert result.selected_provider == "openai"
    assert result.selected_model == "gpt-4.1-mini"
    assert result.selected_tools == ["read_file"]


def test_apply_beta_falls_back_to_heuristic_when_llm_call_fails(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "read_file", "summary": "read file", "tags": ["read", "file"]}],
            "skills": [{"id": "code_review", "summary": "review code", "tags": ["review", "code"]}],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("llm down")),
    )
    result = apply_beta_context_protocol(
        prompt="please review and read files",
        beta_cfg=_base_beta(selector_confidence_threshold=0.45),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.fallback_used is False
    assert "read_file" in result.selected_tools


def test_selector_prunes_browser_tools_without_browser_intent(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "browser_navigate", "summary": "browse", "tags": ["browser"]},
                {"id": "read_file", "summary": "read", "tags": ["read", "file"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [
                {"id": "browser_navigate", "relevance": 0.95, "reason": "wrong"},
                {"id": "read_file", "relevance": 0.9, "reason": "needed"},
            ],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "mixed",
        },
    )
    result = apply_beta_context_protocol(
        prompt="read local repository files and summarize",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert "browser_navigate" not in result.selected_tools
    assert "read_file" in result.selected_tools


def test_selector_prunes_low_relevance_tools(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "read_file", "summary": "read", "tags": ["read"]},
                {"id": "patch", "summary": "patch", "tags": ["patch"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [
                {"id": "read_file", "relevance": 0.7, "reason": "needed"},
                {"id": "patch", "relevance": 0.4, "reason": "weak"},
            ],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "scored",
        },
    )
    result = apply_beta_context_protocol(
        prompt="inspect files only",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.selected_tools == ["read_file"]


def test_selector_recovery_keeps_low_relevance_required_tool(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "search_files", "summary": "search repo", "tags": ["search", "repo"]},
                {"id": "read_file", "summary": "read file", "tags": ["read", "file"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [
                {"id": "search_files", "relevance": 0.30, "reason": "low but needed"},
            ],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "scored",
        },
    )
    result = apply_beta_context_protocol(
        prompt="find where this function is defined",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert "search_files" in result.selected_tools


def test_selector_recovery_adds_minimum_tool_for_medium_complexity(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "search_files", "summary": "search repo", "tags": ["search", "repo"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "none",
        },
    )
    result = apply_beta_context_protocol(
        prompt="debug this code path",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.selected_tools == ["search_files"]


def test_baseline_required_tools_are_non_prunable(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "search_files", "summary": "search repo", "tags": ["search", "repo"]},
                {"id": "read_file", "summary": "read file", "tags": ["read", "file"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [
                {"id": "search_files", "relevance": 0.10, "reason": "too low"},
            ],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "llm weak",
        },
    )
    result = apply_beta_context_protocol(
        prompt="find where this code path is implemented",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert "search_files" in result.selected_tools


def test_baseline_merges_with_llm_and_prunes_optional(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "search_files", "summary": "search repo", "tags": ["search", "repo"]},
                {"id": "read_file", "summary": "read file", "tags": ["read", "file"]},
                {"id": "skill_view", "summary": "view skill", "tags": ["skill"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [
                {"id": "search_files", "relevance": 0.9, "reason": "needed"},
                {"id": "read_file", "relevance": 0.9, "reason": "needed"},
                {"id": "skill_view", "relevance": 0.2, "reason": "weak"},
            ],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "mixed",
        },
    )
    result = apply_beta_context_protocol(
        prompt="find and update this file in codebase",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert "search_files" in result.selected_tools
    assert "read_file" in result.selected_tools
    assert "skill_view" not in result.selected_tools


def test_baseline_adds_patch_and_todo_for_implementation_tasklist_prompt(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [
                {"id": "search_files", "summary": "search repo", "tags": ["search", "repo"]},
                {"id": "read_file", "summary": "read file", "tags": ["read", "file"]},
                {"id": "patch", "summary": "edit files", "tags": ["edit", "write"]},
                {"id": "todo", "summary": "todo list", "tags": ["todo", "task"]},
            ],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "none",
        },
    )
    result = apply_beta_context_protocol(
        prompt="implement this fix and update todo task list",
        beta_cfg=_base_beta(),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert "patch" in result.selected_tools
    assert "todo" in result.selected_tools


def test_active_mode_gate_forces_shadow_without_benchmark_pass(monkeypatch):
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "search_files", "summary": "search", "tags": ["search"]}],
            "skills": [],
        },
    )
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter._llm_decision_call",
        lambda **kwargs: {
            "selected_tools": [{"id": "search_files", "relevance": 0.9, "reason": "needed"}],
            "selected_skills": [],
            "complexity": "medium",
            "confidence": 0.9,
            "reason": "ok",
        },
    )
    result = apply_beta_context_protocol(
        prompt="search for code path",
        beta_cfg=_base_beta(
            skill_tool_context_protocol_mode="active",
            shadow_benchmark_passed=False,
            decision_diagnostics_enabled=True,
            active_local_dev_only=True,
            fallback_to_manual=True,
        ),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.mode.value == "shadow"
    assert result.selected_tools == []


class _FakeLLMMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLLMChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeLLMMessage(content)


class _FakeLLMResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeLLMChoice(content)]


def test_beta_selector_accepts_session_auth_provider_without_api_key(monkeypatch):
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "search_files", "summary": "search", "tags": ["search"]}],
            "skills": [],
        },
    )

    def _fake_call_llm(**kwargs):
        captured.update(kwargs)
        return _FakeLLMResponse(
            '{"selected_tools":[{"id":"search_files","relevance":0.9,"reason":"needed"}],'
            '"selected_skills":[],"complexity":"medium","confidence":0.9,"reason":"ok"}'
        )

    monkeypatch.setattr("animus.beta.context_protocol.request_adapter.call_llm", _fake_call_llm)
    result = apply_beta_context_protocol(
        prompt="find relevant code paths",
        beta_cfg=_base_beta(
            auto_model_router_enabled=False,
            _inference_provider="cursor-agent",
            _inference_model="gpt-4.1-mini",
            _inference_api_key=None,
            _inference_main_runtime={
                "provider": "cursor-agent",
                "model": "gpt-4.1-mini",
                "api_mode": "chat_completions",
                "api_key": None,
                "command": "cursor-agent",
                "args": [],
            },
        ),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.fallback_used is False
    assert result.selected_tools == ["search_files"]
    assert captured.get("provider") == "cursor-agent"
    assert captured.get("api_key") in (None, "")


def test_beta_selector_uses_current_model_when_router_disabled(monkeypatch):
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "animus.beta.context_protocol.request_adapter.build_registry_snapshot",
        lambda **kwargs: {
            "tools": [{"id": "read_file", "summary": "read", "tags": ["read"]}],
            "skills": [],
        },
    )

    def _fake_call_llm(**kwargs):
        captured.update(kwargs)
        return _FakeLLMResponse(
            '{"selected_tools":[{"id":"read_file","relevance":0.9,"reason":"needed"}],'
            '"selected_skills":[],"complexity":"medium","confidence":0.9,"reason":"ok"}'
        )

    monkeypatch.setattr("animus.beta.context_protocol.request_adapter.call_llm", _fake_call_llm)
    result = apply_beta_context_protocol(
        prompt="open and summarize this file",
        beta_cfg=_base_beta(
            auto_model_router_enabled=False,
            _inference_provider="claude-code",
            _inference_model="claude-sonnet-4",
            _inference_main_runtime={
                "provider": "claude-code",
                "model": "claude-sonnet-4",
                "api_mode": "chat_completions",
                "api_key": None,
                "command": "claude",
                "args": [],
            },
        ),
        enabled_toolsets=["hermes-api-server"],
        disabled_tools=[],
        candidates=[{"provider": "openai", "model": "gpt-4.1-mini"}],
    )
    assert result.fallback_used is False
    assert result.selected_tools == ["read_file"]
    assert captured.get("provider") == "claude-code"
    assert captured.get("model") == "claude-sonnet-4"

