"""D-142P3 Command Center stale/freshness UI contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"
EPHEMERAL_BROWSER_SLUG_PREFIX = "cc-browser-test-"


class CommandCenterD142P3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.index_html = (APP_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")

    def test_archive_stale_button_present(self) -> None:
        self.assertIn('id="ccArchiveStaleBtn"', self.index_html)
        self.assertIn("archiveStaleGoalsForProject", self.app_js)

    def test_archive_stale_calls_real_api(self) -> None:
        chunk = self.app_js.split("async function archiveStaleGoalsForProject")[1].split(
            "function updateArchiveStaleButton"
        )[0]
        self.assertIn("goals/archive-stale", chunk)
        self.assertIn("dry_run: true", chunk)
        self.assertIn("dry_run: false", chunk)
        self.assertNotIn("mock", chunk.lower())

    def test_freshness_display_and_filter_hooks(self) -> None:
        for symbol in (
            "platformStaleGoalCount",
            "visiblePlatformGoals",
            "cc-goal-freshness-stale",
            "goal.freshness === 'stale'",
            "stale_count",
        ):
            self.assertIn(symbol, self.app_js)

    def test_honest_archive_error_surface(self) -> None:
        chunk = self.app_js.split("async function archiveStaleGoalsForProject")[1].split(
            "function updateArchiveStaleButton"
        )[0]
        self.assertIn("catch (err)", chunk)
        self.assertIn("window.alert(String(err.message", chunk)

    def test_ephemeral_browser_slug_isolation_documented(self) -> None:
        self.assertTrue(EPHEMERAL_BROWSER_SLUG_PREFIX.startswith("cc-browser-test-"))


if __name__ == "__main__":
    unittest.main()
