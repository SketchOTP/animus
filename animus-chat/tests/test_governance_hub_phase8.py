"""Phase 8 Driver panel helper contract tests (mirrors governance-hub.js helpers)."""

from __future__ import annotations

import unittest


def parse_driver_status(data: dict) -> dict:
    if not isinstance(data, dict):
        return {
            "status": "idle",
            "active_goal_id": None,
            "active_queue_entry_id": None,
            "last_stop_reason": None,
        }
    return {
        "status": str(data.get("status") or "idle"),
        "active_goal_id": data.get("active_goal_id"),
        "active_queue_entry_id": data.get("active_queue_entry_id"),
        "last_stop_reason": data.get("last_stop_reason"),
        "last_seq": data.get("last_seq"),
    }


def format_driver_status(driver: dict) -> str:
    return str(driver.get("status") or "idle")


def format_budget_hint(driver: dict) -> str:
    reason = str(driver.get("last_stop_reason") or "")
    if "budget" in reason or reason == "budget_exceeded":
        return "Budget cap reached (run count or wall-clock)"
    return "Budget: registry policy (run count + wall-clock)"


def should_show_sign_off(goal_status: str) -> bool:
    return str(goal_status or "") == "pending_completion"


def build_hierarchy_summary(milestones_payload: dict, queue_payload: dict) -> dict:
    milestones = milestones_payload.get("milestones") or []
    phases = milestones_payload.get("phases") or []
    queue = queue_payload.get("queue_entries") or []
    if not isinstance(milestones, list):
        milestones = []
    if not isinstance(phases, list):
        phases = []
    if not isinstance(queue, list):
        queue = []
    return {
        "milestone_count": len(milestones),
        "phase_count": len(phases),
        "queue_count": len(queue),
        "ready_count": sum(1 for row in queue if row.get("materialization") == "ready"),
        "dispatched_count": sum(1 for row in queue if row.get("materialization") == "dispatched"),
        "completed_count": sum(1 for row in queue if row.get("materialization") == "completed"),
    }


class GovernanceHubPhase8Tests(unittest.TestCase):
    def test_parse_driver_status_idle(self) -> None:
        parsed = parse_driver_status({})
        self.assertEqual(parsed["status"], "idle")
        self.assertIsNone(parsed["active_goal_id"])

    def test_parse_driver_status_running(self) -> None:
        parsed = parse_driver_status(
            {
                "status": "running",
                "active_goal_id": "g1",
                "active_queue_entry_id": "q1",
                "last_stop_reason": None,
            }
        )
        self.assertEqual(parsed["status"], "running")
        self.assertEqual(parsed["active_goal_id"], "g1")

    def test_format_budget_hint_default(self) -> None:
        self.assertIn("registry policy", format_budget_hint({"last_stop_reason": None}))

    def test_format_budget_hint_exceeded(self) -> None:
        self.assertIn("Budget cap", format_budget_hint({"last_stop_reason": "budget_exceeded"}))

    def test_should_show_sign_off(self) -> None:
        self.assertTrue(should_show_sign_off("pending_completion"))
        self.assertFalse(should_show_sign_off("active"))

    def test_hierarchy_dispatch_counts(self) -> None:
        summary = build_hierarchy_summary(
            {"milestones": [], "phases": []},
            {
                "queue_entries": [
                    {"materialization": "ready"},
                    {"materialization": "dispatched"},
                    {"materialization": "completed"},
                ]
            },
        )
        self.assertEqual(summary["ready_count"], 1)
        self.assertEqual(summary["dispatched_count"], 1)
        self.assertEqual(summary["completed_count"], 1)

    def test_governance_hub_js_exports_driver_helpers(self) -> None:
        from pathlib import Path

        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        text = js_path.read_text(encoding="utf-8")
        self.assertIn("parseDriverStatus", text)
        self.assertIn("renderGovernanceDriver", text)
        self.assertIn("governanceDriverPanel", text)
        self.assertIn("driver/status", text)
        self.assertIn("sign-off", text)
        self.assertIn("data-driver-action", text)


if __name__ == "__main__":
    unittest.main()
