from types import SimpleNamespace
from unittest.mock import patch

from agent.auto_model_by_complexity import select_model_for_turn


def test_disabled_returns_none():
    m, c = select_model_for_turn(
        provider="openrouter",
        baseline_model="anthropic/claude-opus-4.6",
        user_message="hello",
        history_message_count=0,
        enabled_toolset_count=2,
        agent_cfg={"auto_model_by_complexity": False},
    )
    assert m is None and c is None


@patch("agent.auto_model_by_complexity.list_agentic_models")
@patch("agent.auto_model_by_complexity.get_model_info")
def test_low_complexity_picks_cheaper(mock_info, mock_list):
    mock_list.return_value = [
        "anthropic/claude-haiku-4.5",
        "anthropic/claude-sonnet-4.6",
        "anthropic/claude-opus-4.6",
    ]

    def _info(_p, mid):
        costs = {
            "anthropic/claude-haiku-4.5": (0.5, 2.0),
            "anthropic/claude-sonnet-4.6": (2.0, 8.0),
            "anthropic/claude-opus-4.6": (10.0, 40.0),
        }
        inp, out = costs[mid]
        return SimpleNamespace(cost_input=inp, cost_output=out, id=mid)

    mock_info.side_effect = _info

    chosen, complexity = select_model_for_turn(
        provider="openrouter",
        baseline_model="anthropic/claude-opus-4.6",
        user_message="quick typo fix",
        history_message_count=0,
        enabled_toolset_count=2,
        agent_cfg={"auto_model_by_complexity": True},
    )
    assert complexity == "low"
    assert chosen is not None
    assert "haiku" in (chosen or "").lower()


@patch("hermes_cli.codex_models.get_codex_model_ids")
def test_openai_codex_uses_codex_catalog_not_models_dev(mock_codex_ids):
    """Codex catalog must come from get_codex_model_ids, not models.dev."""
    mock_codex_ids.return_value = [
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-5.4",
    ]
    chosen, complexity = select_model_for_turn(
        provider="openai-codex",
        baseline_model="gpt-5.4",
        user_message="quick typo fix",
        history_message_count=0,
        enabled_toolset_count=2,
        agent_cfg={"auto_model_by_complexity": True},
        codex_access_token="test-token",
    )
    mock_codex_ids.assert_called_once_with(access_token="test-token")
    assert complexity == "low"
    assert chosen == "gpt-5.4-mini"


@patch("hermes_cli.codex_models.get_codex_model_ids")
def test_openai_codex_high_complexity_biases_heavier(mock_codex_ids):
    mock_codex_ids.return_value = [
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-5.4",
    ]
    chosen, complexity = select_model_for_turn(
        provider="openai-codex",
        baseline_model="gpt-5.4-mini",
        user_message=(
            "Refactor the entire payment module, add property tests, migrate DB "
            "schema, and document the security threat model."
        ),
        history_message_count=40,
        enabled_toolset_count=12,
        agent_cfg={"auto_model_by_complexity": True},
    )
    assert complexity == "high"
    assert chosen in ("gpt-5.4", "gpt-5.3-codex")
    assert chosen != "gpt-5.4-mini"
