"""D-141 Dedicated Command Center API integration contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD141Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.index_html = (APP_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")
        self.styles_css = (APP_DIR / "styles.css").read_text(encoding="utf-8")

    def test_project_registry_fetch_and_render(self) -> None:
        self.assertIn("govFetch('projects')", self.app_js)
        self.assertIn("projects/' + encodeURIComponent", self.app_js)
        self.assertIn("ccProjectGrid", self.index_html)
        self.assertIn("formatProjectRegistryMeta", self.app_js)
        self.assertIn("architect_import_status", self.app_js)
        self.assertIn("default_validator", self.app_js)
        self.assertIn("memory_mode", self.app_js)
        self.assertIn("dirty_tree", self.app_js)

    def test_goal_runner_form_controls_present(self) -> None:
        static_ids = ("ccGoalRunnerTimeline", "ccGoalRunnerPanels", "ccGoalRunnerControls")
        for element_id in static_ids:
            self.assertIn(f'id="{element_id}"', self.index_html)
        dynamic_ids = (
            "ccGoalRunnerPanel",
            "ccGoalRunnerProject",
            "ccGoalRunnerStatement",
            "ccGoalRunnerRun",
            "ccGoalRunnerRefresh",
        )
        for element_id in dynamic_ids:
            self.assertIn(f'id="{element_id}"', self.app_js)
        self.assertIn('data-goal-runner-field="run_mode"', self.app_js)
        self.assertIn('data-goal-runner-field="research_mode"', self.app_js)
        self.assertIn('data-goal-runner-field="approval_mode"', self.app_js)

    def test_goal_run_payload_is_correct(self) -> None:
        self.assertIn("buildGoalRunPayload", self.app_js)
        self.assertIn("submitProjectGoalRun", self.app_js)
        self.assertIn("goal-runs", self.app_js)
        self.assertIn("budget_override", self.app_js)
        self.assertIn("run_mode", self.app_js)
        self.assertIn("research_mode", self.app_js)
        self.assertIn("approval_mode", self.app_js)
        self.assertIn("method: 'POST'", self.app_js)

    def test_draft_only_submission_renders_goal_run_id(self) -> None:
        self.assertIn("goal_run_id", self.app_js)
        self.assertIn("Run draft_only", self.app_js)
        self.assertIn("draft_only", self.app_js)

    def test_timeline_renders_states(self) -> None:
        self.assertIn("TIMELINE_STATES", self.app_js)
        self.assertIn("buildTimelineHtml", self.app_js)
        self.assertIn("awaiting_approval", self.app_js)
        self.assertIn("entry_dispatched", self.app_js)

    def test_research_breakdown_outcome_panels_render_api_fields(self) -> None:
        self.assertIn("buildResearchPanelHtml", self.app_js)
        self.assertIn("research_status", self.app_js)
        self.assertIn("buildBreakdownPanelHtml", self.app_js)
        self.assertIn("allowed files", self.app_js)
        self.assertIn("buildOutcomePanelHtml", self.app_js)
        self.assertIn("Pending final review/sign-off", self.app_js)

    def test_run_mode_warning_visible(self) -> None:
        self.assertIn("shouldShowRunModeWarning", self.app_js)
        self.assertIn("Full run mode may start Driver", self.app_js)

    def test_no_self_sign_off_action(self) -> None:
        chunk = self.app_js.split("async function submitProjectGoalRun")[1].split("async function refreshGoalRunnerView")[0]
        self.assertNotIn("signOffGoal", chunk)
        self.assertNotIn("governanceDriverSignOff", chunk)
        self.assertIn("No self-sign-off from Goal Runner", self.app_js)

    def test_driver_controls_remain_disabled(self) -> None:
        self.assertIn("Driver controls disabled", self.app_js)
        self.assertIn("disabled", self.app_js.split("renderDriver")[1].split("function renderRelease")[0])

    def test_goal_run_detail_endpoints(self) -> None:
        self.assertIn("goal-runs/' + encodeURIComponent", self.app_js)
        self.assertIn("goals/' + encodeURIComponent", self.app_js)
        self.assertIn("driverStatusPath()", self.app_js)

    def test_evidence_links_supported(self) -> None:
        self.assertIn("cc-evidence-link", self.app_js)
        self.assertIn("evidence_refs", self.app_js)


if __name__ == "__main__":
    unittest.main()
