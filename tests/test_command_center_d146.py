"""D-146 Command Center multi-entry queue and pending_completion display tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD146Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")

    def test_queue_shows_multiple_entries_with_release_and_commit(self) -> None:
        chunk = self.app_js.split("buildBreakdownHierarchyHtml: function")[1].split("computeDriverLaunchGate")[0]
        self.assertIn("queue.map", chunk)
        self.assertIn("entry.release_status", chunk)
        self.assertIn("entry.commit_sha", chunk)
        self.assertIn("entry.run_id", chunk)

    def test_pending_completion_shows_sign_off_without_auto_trigger(self) -> None:
        self.assertIn("pending_completion", self.app_js)
        self.assertIn("shouldShowGoalSignOff", self.app_js)
        self.assertIn("data-goal-action=\"sign-off\"", self.app_js)
        self.assertNotIn("signOffGoal(", self.app_js.split("buildGoalCardHtml: function")[0])


if __name__ == "__main__":
    unittest.main()
