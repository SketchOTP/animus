"""D-144 Command Center launch readiness mirror contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD144Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")

    def test_launch_readiness_fetched_from_governance_api(self) -> None:
        self.assertIn("fetchDriverLaunchReadiness", self.app_js)
        self.assertIn("driver/launch-readiness", self.app_js)
        self.assertIn("launchReadinessCache", self.app_js)

    def test_compute_driver_launch_gate_prefers_api_readiness(self) -> None:
        gate_chunk = self.app_js.split("computeDriverLaunchGate: function")[1].split("buildLaunchReadinessPanelHtml")[0]
        self.assertIn("ctx.readiness", gate_chunk)
        self.assertIn("readiness.ready", gate_chunk)
        self.assertIn("blocking_reason", gate_chunk)

    def test_launch_block_reason_rendered_in_ui(self) -> None:
        self.assertIn("buildLaunchReadinessPanelHtml", self.app_js)
        self.assertIn("cc-launch-readiness-block", self.app_js)
        self.assertIn("cc-driver-launch-block", self.app_js)

    def test_start_action_refreshes_readiness_before_launch(self) -> None:
        handler = self.app_js.split("if (action === 'start')")[1].split("await postDriverControl")[0]
        self.assertIn("fetchDriverLaunchReadiness", handler)


if __name__ == "__main__":
    unittest.main()
