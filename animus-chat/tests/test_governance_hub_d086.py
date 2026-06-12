"""D-086 goal intake + breakdown approval UI contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path


class GovernanceHubD086Tests(unittest.TestCase):
    def test_governance_hub_js_exports_intake_and_approval_helpers(self) -> None:
        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        text = js_path.read_text(encoding="utf-8")
        self.assertIn("governanceGoalIntakePanel", text)
        self.assertIn("governanceGoalIntakeSubmit", text)
        self.assertIn("governanceBreakdownReview", text)
        self.assertIn("governanceGoalApprove", text)
        self.assertIn("governanceGoalReject", text)
        self.assertIn("submitGoalIntake", text)
        self.assertIn("approveGoalBreakdown", text)
        self.assertIn("rejectGoalBreakdown", text)
        self.assertIn("shouldShowBreakdownApproval", text)
        self.assertIn("formatBudgetCaps", text)

    def test_intake_form_fields_present(self) -> None:
        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        text = js_path.read_text(encoding="utf-8")
        for field in (
            'data-intake-field="statement"',
            'data-intake-field="repo_path"',
            'data-intake-field="include_memory"',
            'data-intake-field="include_research"',
            'data-intake-field="goal_size_hint"',
            'data-intake-field="tier_expectation"',
            'data-intake-field="chk_breakdown"',
        ):
            self.assertIn(field, text)

    def test_intake_and_approval_fetch_paths(self) -> None:
        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        text = js_path.read_text(encoding="utf-8")
        self.assertIn("govFetch('goals',", text)
        self.assertIn("/breakdown/approve", text)
        self.assertIn("/breakdown/reject", text)
        self.assertNotIn("driver/start", text.split("submitGoalIntake")[1].split("renderGoalIntakeForm")[0])


if __name__ == "__main__":
    unittest.main()
