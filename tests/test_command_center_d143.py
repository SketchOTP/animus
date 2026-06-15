"""D-143 Command Center governed goal intake contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD143Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")
        self.styles_css = (APP_DIR / "styles.css").read_text(encoding="utf-8")

    def test_goal_intake_posts_to_governance_goals_api(self) -> None:
        chunk = self.app_js.split("async function submitGoalIntake")[1].split("async function submitProjectGoalRun")[0]
        payload_chunk = self.app_js.split("buildGoalIntakePayload: function")[1].split("goalIntakePostPath")[0]
        self.assertIn("buildGoalIntakePayload", self.app_js)
        self.assertIn("goalIntakePostPath", self.app_js)
        self.assertIn("'goals'", self.app_js)
        self.assertIn("include_memory", payload_chunk)
        self.assertIn("include_research", payload_chunk)
        self.assertIn("budget_override", payload_chunk)
        self.assertIn("buildGoalIntakePayload", chunk)
        self.assertNotIn("goal-runs", chunk)

    def test_intake_form_exposes_memory_research_and_budget_fields(self) -> None:
        form_chunk = self.app_js.split("async function renderGoalRunnerForm")[1].split("async function submitGoalIntake")[0]
        self.assertIn("ccGoalRunnerIncludeMemory", form_chunk)
        self.assertIn("ccGoalRunnerIncludeResearch", form_chunk)
        self.assertIn("ccGoalRunnerMaxRuns", form_chunk)
        self.assertIn("ccGoalRunnerMaxHours", form_chunk)
        self.assertIn("Create goal", form_chunk)
        self.assertNotIn("Full run — through execution", form_chunk)

    def test_breakdown_hierarchy_and_approval_state_rendered(self) -> None:
        for symbol in (
            "buildBreakdownHierarchyHtml",
            "approval_state",
            "proposed_tiers",
            "non_dispatch_reason",
            "/milestones",
            "cc-breakdown-tree",
        ):
            self.assertIn(symbol, self.app_js if symbol != "cc-breakdown-tree" else self.styles_css)

    def test_driver_launch_gated_on_approval_and_clean_tree(self) -> None:
        self.assertIn("computeDriverLaunchGate", self.app_js)
        gate_chunk = self.app_js.split("computeDriverLaunchGate: function")[1].split("buildResearchPanelHtml")[0]
        self.assertIn("dirty.blocking", gate_chunk)
        self.assertIn("pending_approval", gate_chunk)
        self.assertIn("dispatchable", gate_chunk)
        handler = self.app_js.split("if (action === 'start')")[1].split("await postDriverControl")[0]
        self.assertIn("computeDriverLaunchGate", handler)

    def test_approve_and_reject_use_governed_endpoints(self) -> None:
        self.assertIn("breakdown/approve", self.app_js)
        self.assertIn("breakdown/reject", self.app_js)
        self.assertIn("reject-breakdown", self.app_js)
        self.assertNotIn("mockGoal", self.app_js.lower())
        self.assertNotIn("registry.json", self.app_js)

    def test_no_auto_driver_on_goal_create(self) -> None:
        chunk = self.app_js.split("async function submitGoalIntake")[1].split("async function submitProjectGoalRun")[0]
        self.assertNotIn("postDriverControl", chunk)
        self.assertNotIn("driver/start", chunk)
        self.assertIn("Driver not started", chunk)


if __name__ == "__main__":
    unittest.main()
