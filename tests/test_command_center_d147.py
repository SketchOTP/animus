"""D-147 Command Center operator sign-off UI tests."""

from __future__ import annotations

import unittest
from pathlib import Path


class CommandCenterD147Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app_js = (Path(__file__).resolve().parents[1] / "animus-command-center" / "app" / "app.js").read_text(
            encoding="utf-8"
        )

    def test_sign_off_readiness_fetch(self) -> None:
        self.assertIn("fetchSignOffReadiness", self.app_js)
        self.assertIn("sign-off-readiness", self.app_js)

    def test_compute_sign_off_gate_prefers_api(self) -> None:
        chunk = self.app_js.split("computeSignOffGate")[1].split("buildSignOffReadinessPanelHtml")[0]
        self.assertIn("readiness.ready === false", chunk)
        self.assertIn("readiness.ready === true", chunk)

    def test_sign_off_button_gated_by_readiness(self) -> None:
        chunk = self.app_js.split("buildGoalApprovalPanelHtml")[1].split("refreshAfterGovernanceAction")[0]
        self.assertIn("signOffGate.ok", chunk)
        self.assertIn("computeSignOffGate", chunk)

    def test_post_sign_off_includes_operator_actor(self) -> None:
        chunk = self.app_js.split("postGoalSignOff")[1].split("postBreakdownApprove")[0]
        self.assertIn("actor: 'operator'", chunk)
        self.assertIn("source: 'command_center'", chunk)

    def test_completion_metadata_panel(self) -> None:
        self.assertIn("buildCompletionMetadataHtml", self.app_js)
        self.assertIn("Goal completed", self.app_js)

    def test_sign_off_click_checks_gate_before_post(self) -> None:
        handler = self.app_js.split("wireGovernanceActionsOnce")[1].split("renderOverviewBody")[0]
        self.assertIn("fetchSignOffReadiness", handler)
        self.assertIn("computeSignOffGate", handler)
