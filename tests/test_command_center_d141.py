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
        self.assertIn("ccGoalRunnerIncludeMemory", self.app_js)
        self.assertIn("ccGoalRunnerIncludeResearch", self.app_js)
        self.assertIn("submitGoalIntake", self.app_js)

    def test_goal_run_payload_is_correct(self) -> None:
        self.assertIn("buildGoalIntakePayload", self.app_js)
        self.assertIn("submitGoalIntake", self.app_js)
        self.assertIn("include_memory", self.app_js)
        self.assertIn("include_research", self.app_js)
        self.assertIn("budget_override", self.app_js)
        self.assertIn("method: 'POST'", self.app_js)

    def test_draft_only_submission_renders_goal_run_id(self) -> None:
        self.assertIn("goal_run_id", self.app_js)
        self.assertIn("Create goal", self.app_js)
        self.assertIn("Driver not started", self.app_js)

    def test_goal_statement_help_tooltip(self) -> None:
        self.assertIn("GOAL_STATEMENT_HELP", self.app_js)
        self.assertIn("cc-info-btn", self.app_js)
        self.assertIn("RESEARCH_HELP", self.app_js)
        self.assertIn("APPROVAL_HELP", self.app_js)

    def test_goal_runner_shows_project_activity(self) -> None:
        self.assertIn("ccGoalList", self.index_html)
        self.assertIn("ccGoalNewGoalCollapsible", self.index_html)
        self.assertIn("runsForGoal", self.app_js)
        self.assertIn("r.goal_id", self.app_js)
        self.assertIn("cc-stat-scope", self.styles_css)
        self.assertIn("cc-goal-new-collapsible", self.styles_css)
        self.assertIn("loadGoalRunnerProjectActivity", self.app_js)
        self.assertIn("renderGoalList", self.app_js)
        self.assertIn("viewGoalLifecycle", self.app_js)
        self.assertIn("ccProjectAddBtn", self.index_html)
        self.assertIn("ccProjectModal", self.index_html)
        self.assertIn("openProjectEditor", self.app_js)
        self.assertIn("method: 'POST'", self.app_js.split("async function saveProject")[1].split("function wireProjectEditorChrome")[0])
        self.assertIn("projects/' + encodeURIComponent(state.projectEditor.projectId) + '/update'", self.app_js)
        self.assertIn("Add project", self.index_html)

    def test_timeline_renders_states(self) -> None:
        self.assertIn("TIMELINE_STATES", self.app_js)
        self.assertIn("buildTimelineHtml", self.app_js)
        self.assertIn("awaiting_approval", self.app_js)
        self.assertIn("entry_dispatched", self.app_js)

    def test_research_breakdown_outcome_panels_render_api_fields(self) -> None:
        self.assertIn("buildResearchPanelHtml", self.app_js)
        self.assertIn("research_status", self.app_js)
        self.assertIn("buildBreakdownPanelHtml", self.app_js)
        self.assertIn("approval_state", self.app_js)
        self.assertIn("buildBreakdownHierarchyHtml", self.app_js)
        self.assertIn("buildOutcomePanelHtml", self.app_js)
        self.assertIn("Pending final review/sign-off", self.app_js)

    def test_run_mode_warning_visible(self) -> None:
        self.assertIn("shouldShowRunModeWarning", self.app_js)
        self.assertIn("Full run mode may start Driver", self.app_js)

    def test_no_auto_sign_off_on_goal_submit(self) -> None:
        chunk = self.app_js.split("async function submitGoalIntake")[1].split("async function submitProjectGoalRun")[0]
        self.assertNotIn("postGoalSignOff", chunk)
        self.assertNotIn("signOffGoal", chunk)
        self.assertNotIn("postDriverControl", chunk)
        self.assertIn("postGoalSignOff", self.app_js)
        self.assertIn("data-goal-action=\"sign-off\"", self.app_js)
        self.assertIn("buildGoalApprovalPanelHtml", self.app_js)
        self.assertIn("wireGovernanceActionsOnce", self.app_js)
        self.assertIn("governanceActionInFlight", self.app_js)
        self.assertNotIn("wireDriverControls", self.app_js)
        self.assertNotIn("enrichDriverOverviewPanel", self.app_js)

    def test_governance_actions_use_single_delegated_handler(self) -> None:
        self.assertIn("dataset.govActionsWired", self.app_js)
        self.assertIn("refreshAfterGovernanceAction", self.app_js)
        self.assertIn("mergeProjectGoalsAndRuns", self.app_js)
        self.assertIn("ccGoalApprovalPanel", self.app_js)
        self.assertIn("window.confirm", self.app_js)
        self.assertIn("cc-approval-panel", self.styles_css)

    def test_runs_show_project_and_full_progress(self) -> None:
        self.assertIn("_project_name", self.app_js)
        self.assertIn("runProgressPct", self.app_js)
        self.assertIn("return 100", self.app_js.split("function runProgressPct")[1].split("function runBarColor")[0])

    def test_tab_scoped_goals_layout(self) -> None:
        self.assertIn("ccGoalsProjectSelect", self.index_html)
        self.assertIn("ccGoalFilterTabs", self.index_html)
        self.assertIn("ccHistoryProjectSelect", self.index_html)
        self.assertIn("ccPanelHistory", self.index_html)
        self.assertIn("renderGoalFilterTabs", self.app_js)
        self.assertIn("buildInlineApprovalHtml", self.app_js)
        self.assertIn("buildGoalQuickActionsHtml", self.app_js)
        self.assertIn("loadHistoryForProject", self.app_js)
        self.assertIn("buildSimpleProgressHtml", self.app_js)
        self.assertIn("GOAL_FILTER_TABS", self.app_js)
        self.assertIn(".cc-goal-card", self.styles_css)
        self.assertIn(".cc-history-item", self.styles_css)

    def test_driver_controls_in_command_center(self) -> None:
        self.assertIn("postDriverControl", self.app_js)
        self.assertIn("data-driver-action", self.app_js)
        self.assertIn("The Driver is the autonomous executor", self.app_js)
        self.assertNotIn("Controls live in Animus Chat", self.app_js)
        self.assertNotIn("Animus Chat", self.app_js)

    def test_goal_run_detail_endpoints(self) -> None:
        self.assertIn("goal-runs/' + encodeURIComponent", self.app_js)
        self.assertIn("goals/' + encodeURIComponent", self.app_js)
        self.assertIn("driverStatusPath()", self.app_js)

    def test_evidence_links_supported(self) -> None:
        self.assertIn("cc-evidence-link", self.app_js)
        self.assertIn("evidence_refs", self.app_js)


if __name__ == "__main__":
    unittest.main()
