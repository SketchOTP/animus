"""Phase 7 Goals tab helper contract tests (mirrors governance-hub.js helpers)."""

from __future__ import annotations

import unittest


def parse_goals_list(data: dict) -> list:
    goals = data.get("goals")
    return goals if isinstance(goals, list) else []


def format_goal_status(goal: dict) -> str:
    return str(goal.get("status") or "unknown")


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
    }


class GovernanceHubPhase7Tests(unittest.TestCase):
    def test_parse_goals_list_empty(self) -> None:
        self.assertEqual(parse_goals_list({}), [])
        self.assertEqual(parse_goals_list({"goals": None}), [])

    def test_parse_goals_list_rows(self) -> None:
        data = {"goals": [{"goal_id": "g1", "status": "active"}]}
        self.assertEqual(len(parse_goals_list(data)), 1)

    def test_format_goal_status_default(self) -> None:
        self.assertEqual(format_goal_status({}), "unknown")
        self.assertEqual(format_goal_status({"status": "pending_approval"}), "pending_approval")

    def test_build_hierarchy_summary_ready_count(self) -> None:
        summary = build_hierarchy_summary(
            {"milestones": [{"milestone_id": "m1"}], "phases": [{"phase_id": "p1"}]},
            {
                "queue_entries": [
                    {"materialization": "pending", "ordinal": 1},
                    {"materialization": "ready", "ordinal": 2},
                ]
            },
        )
        self.assertEqual(summary["milestone_count"], 1)
        self.assertEqual(summary["phase_count"], 1)
        self.assertEqual(summary["queue_count"], 2)
        self.assertEqual(summary["ready_count"], 1)

    def test_governance_hub_js_exports_helpers(self) -> None:
        from pathlib import Path

        js_path = Path(__file__).resolve().parents[1] / "app" / "governance-hub.js"
        text = js_path.read_text(encoding="utf-8")
        self.assertIn("AnimusGovernanceHelpers", text)
        self.assertIn("renderGovernanceGoals", text)
        self.assertIn("goals?project_id=", text)


if __name__ == "__main__":
    unittest.main()
