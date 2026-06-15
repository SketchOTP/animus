"""D-140 Dedicated Command Center shell contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"
SERVER_PATH = REPO_ROOT / "animus-command-center" / "server.py"


class CommandCenterD140Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.index_html = (APP_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")
        self.styles_css = (APP_DIR / "styles.css").read_text(encoding="utf-8")
        self.icons_js = (APP_DIR / "icons.js").read_text(encoding="utf-8")
        self.charts_js = (APP_DIR / "charts.js").read_text(encoding="utf-8")
        self.server_py = SERVER_PATH.read_text(encoding="utf-8")

    def test_shell_layout_ids_present(self) -> None:
        for element_id in (
            "ccShell",
            "ccSidebar",
            "ccNav",
            "ccPanelOverview",
            "ccPanelProjects",
            "ccPanelGoals",
            "ccPanelHistory",
            "ccGoalList",
            "ccGoalFilterTabs",
            "ccGoalsProjectSelect",
            "ccGoalNewGoalCollapsible",
            "ccHistoryList",
            "ccOverviewBody",
            "ccStatGrid",
            "ccBrandMark",
        ):
            self.assertIn(f'id="{element_id}"', self.index_html)

    def test_ghost_icon_linked(self) -> None:
        self.assertIn('src="/ghostonlyicon.png"', self.index_html)
        self.assertIn('href="/ghostonlyicon.png"', self.index_html)
        self.assertTrue((APP_DIR / "ghostonlyicon.png").is_file())

    def test_visual_assets_linked(self) -> None:
        self.assertIn('href="/styles.css"', self.index_html)
        self.assertIn('src="/icons.js"', self.index_html)
        self.assertIn('src="/charts.js"', self.index_html)
        self.assertIn('src="/app.js"', self.index_html)

    def test_animus_purple_theme_tokens_in_css(self) -> None:
        self.assertIn("--cc-accent: #7c3aed", self.styles_css)
        self.assertIn(".cc-stat-grid", self.styles_css)
        self.assertIn(".cc-nav-btn", self.styles_css)

    def test_icon_and_chart_modules_export_globals(self) -> None:
        self.assertIn("CCIcons", self.icons_js)
        self.assertIn("CCCharts", self.charts_js)
        self.assertIn("drawSparkline", self.charts_js)
        self.assertIn("drawDonut", self.charts_js)

    def test_app_fetches_governance_read_endpoints(self) -> None:
        self.assertIn("govFetch('projects')", self.app_js)
        self.assertIn("loadGoalsAndRunsAcrossProjects", self.app_js)
        self.assertIn("goals?project_id=", self.app_js)
        self.assertIn("runs?limit=24&project_id=", self.app_js)
        self.assertIn("driverStatusPath()", self.app_js)
        self.assertIn("driver/status?workspace_id=", self.app_js)
        self.assertIn("/api/governance/", self.app_js)

    def test_navigation_sections_defined(self) -> None:
        for section in ("overview", "projects", "goals", "history"):
            self.assertIn(section, self.app_js)
        self.assertNotIn("{ id: 'driver'", self.app_js)
        self.assertNotIn("{ id: 'release'", self.app_js)

    def test_overview_renders_labeled_stats_and_driver(self) -> None:
        self.assertIn("renderDriverPanelHost", self.app_js)
        self.assertIn("driverStatusLabel", self.app_js)
        self.assertIn("Projects", self.app_js)
        self.assertIn("renderGoalList", self.app_js)
        self.assertIn("buildGoalCardHtml", self.app_js)
        self.assertIn("cc-stat-scope", self.styles_css)
        self.assertNotIn("function renderDriver(", self.app_js)

    def test_server_reuses_governance_hub_proxy(self) -> None:
        self.assertIn("governance_hub_route_table", self.server_py)
        self.assertIn("StaticFiles", self.server_py)
        self.assertIn("/healthz", self.server_py)
        self.assertNotIn("animus-chat", self.server_py)

    def test_command_center_desktop_launcher(self) -> None:
        self.assertTrue((REPO_ROOT / "scripts" / "command-center-launch.sh").is_file())
        self.assertTrue((REPO_ROOT / "scripts" / "install-command-center-desktop.sh").is_file())
        launcher = (REPO_ROOT / "scripts" / "command-center-launch.sh").read_text(encoding="utf-8")
        self.assertIn("run-command-center.sh", launcher)
        self.assertIn("ghostonlyicon.png", launcher)

    def test_no_animus_chat_files_touched(self) -> None:
        hub = (REPO_ROOT / "animus-chat" / "app" / "governance-hub.js").read_text(encoding="utf-8")
        self.assertNotIn("ccShell", hub)
        self.assertNotIn("D-140", hub)


if __name__ == "__main__":
    unittest.main()
