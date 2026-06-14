"""D-138 Command Center Goal Runner UI contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path


class GovernanceHubD138Tests(unittest.TestCase):
    def setUp(self) -> None:
        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        self.text = js_path.read_text(encoding="utf-8")

    def test_goal_runner_tab_and_controls_present(self) -> None:
        self.assertIn("governanceTabGoalrunner", self.text)
        self.assertIn("governanceGoalRunnerPanel", self.text)
        self.assertIn("governanceGoalRunnerProject", self.text)
        self.assertIn("governanceGoalRunnerStatement", self.text)
        self.assertIn("governanceGoalRunnerRun", self.text)
        self.assertIn("governanceGoalRunnerRefresh", self.text)
        self.assertIn('data-goal-runner-field="run_mode"', self.text)
        self.assertIn('data-goal-runner-field="research_mode"', self.text)
        self.assertIn('data-goal-runner-field="approval_mode"', self.text)

    def test_project_selector_includes_anima_linux_constant(self) -> None:
        self.assertIn("c9eebdd2-a087-5eae-a074-77b5572fe7b5", self.text)
        self.assertIn("anima-linux", self.text)
        self.assertIn("govFetch('projects')", self.text)

    def test_goal_input_validation_helper(self) -> None:
        self.assertIn("validateGoalStatement", self.text)
        self.assertIn("Goal statement is required", self.text)
        self.assertIn("GOAL_STATEMENT_MAX_LEN", self.text)

    def test_run_posts_to_project_goal_run_api(self) -> None:
        self.assertIn("submitProjectGoalRun", self.text)
        self.assertIn("goal-runs", self.text)
        self.assertIn("goalRunPostPath", self.text)

    def test_payload_includes_modes_and_budget(self) -> None:
        self.assertIn("buildGoalRunPayload", self.text)
        self.assertIn("budget_override", self.text)
        self.assertIn("research_mode", self.text)
        self.assertIn("approval_mode", self.text)
        self.assertIn("run_mode", self.text)

    def test_response_renders_goal_run_and_goal_ids(self) -> None:
        self.assertIn("goal_run_id", self.text)
        self.assertIn("goal_id", self.text)
        self.assertIn("governanceGoalRunnerSummary", self.text)

    def test_timeline_renders_states(self) -> None:
        self.assertIn("TIMELINE_STATES", self.text)
        self.assertIn("buildTimelineHtml", self.text)
        self.assertIn("awaiting_approval", self.text)
        self.assertIn("entry_dispatched", self.text)

    def test_research_panel_renders_scout_fields(self) -> None:
        self.assertIn("buildResearchPanelHtml", self.text)
        self.assertIn("research_status", self.text)
        self.assertIn("research_confidence", self.text)
        self.assertIn("recommended_strategy", self.text)

    def test_breakdown_panel_renders_validator_and_allowed_files(self) -> None:
        self.assertIn("buildBreakdownPanelHtml", self.text)
        self.assertIn("default_validator", self.text)
        self.assertIn("allowed files", self.text)

    def test_blocker_panel_renders_triage_recovery_fields(self) -> None:
        self.assertIn("buildBlockerRecoveryPanelHtml", self.text)
        self.assertIn("blocker_class", self.text)
        self.assertIn("operator_required", self.text)
        self.assertIn("Recovery prepared automatically", self.text)

    def test_memory_panel_renders_mimir_advisory_label(self) -> None:
        self.assertIn("buildMemoryPanelHtml", self.text)
        self.assertIn("Mimir is advisory memory, not approval authority", self.text)
        self.assertIn("memory_refs", self.text)

    def test_outcome_panel_renders_evidence_fields(self) -> None:
        self.assertIn("buildOutcomePanelHtml", self.text)
        self.assertIn("evidence refs", self.text)
        self.assertIn("Pending final review/sign-off", self.text)

    def test_draft_only_driver_not_started_message(self) -> None:
        self.assertIn("draft_only: Driver not started", self.text)

    def test_run_mode_warning_visible(self) -> None:
        self.assertIn("shouldShowRunModeWarning", self.text)
        self.assertIn("Full run mode may start Driver", self.text)

    def test_no_auto_sign_off_in_goal_runner(self) -> None:
        chunk = self.text.split("async function submitProjectGoalRun")[1].split("function wireGovernanceTabsOnce")[0]
        self.assertNotIn("signOffGoal", chunk)
        self.assertNotIn("governanceDriverSignOff", chunk)
        self.assertIn("No self-sign-off from Goal Runner", self.text)


if __name__ == "__main__":
    unittest.main()
