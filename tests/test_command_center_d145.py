"""D-145 Command Center queue release/commit mirror contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD145Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")

    def test_queue_entry_shows_release_status_and_commit_sha(self) -> None:
        chunk = self.app_js.split("buildBreakdownHierarchyHtml: function")[1].split("computeDriverLaunchGate")[0]
        self.assertIn("entry.release_status", chunk)
        self.assertIn("entry.commit_sha", chunk)
        self.assertIn("entry.run_id", chunk)


if __name__ == "__main__":
    unittest.main()
