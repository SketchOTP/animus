"""D-142P2 Command Center project CRUD wiring contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "animus-command-center" / "app"


class CommandCenterD142P2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.index_html = (APP_DIR / "index.html").read_text(encoding="utf-8")
        self.app_js = (APP_DIR / "app.js").read_text(encoding="utf-8")

    def test_project_crud_ui_hooks_present(self) -> None:
        for element_id in ("ccProjectAddBtn", "ccProjectModal", "ccProjectFormHost"):
            self.assertIn(f'id="{element_id}"', self.index_html)
        for symbol in (
            "openProjectEditor",
            "saveProject",
            "readProjectForm",
            "buildProjectFormHtml",
            "wireProjectEditorChrome",
            "ccProjectSaveBtn",
        ):
            self.assertIn(symbol, self.app_js)

    def test_create_calls_governance_post_projects(self) -> None:
        chunk = self.app_js.split("async function saveProject")[1].split("function wireProjectEditorChrome")[0]
        self.assertIn("govFetch('projects',", chunk)
        self.assertIn("method: 'POST'", chunk)
        self.assertIn("'Content-Type': 'application/json'", chunk)

    def test_update_calls_governance_post_update_alias(self) -> None:
        chunk = self.app_js.split("async function saveProject")[1].split("function wireProjectEditorChrome")[0]
        self.assertIn("projects/' + encodeURIComponent(state.projectEditor.projectId) + '/update'", chunk)
        self.assertIn("delete updatePayload.slug", chunk)

    def test_archive_via_status_field(self) -> None:
        self.assertIn("projectSelectOptions(['active', 'bench', 'archived']", self.app_js)
        self.assertIn('id="ccProjectStatus"', self.app_js)

    def test_honest_api_error_surface(self) -> None:
        chunk = self.app_js.split("async function govFetch")[1].split("function setConnection")[0]
        self.assertIn("if (!resp.ok)", chunk)
        self.assertIn("body.detail", chunk)
        save_chunk = self.app_js.split("async function saveProject")[1].split("function wireProjectEditorChrome")[0]
        self.assertIn("errHost.textContent = String(err.message", save_chunk)

    def test_edit_falls_back_to_list_summary_without_profile(self) -> None:
        chunk = self.app_js.split("async function openProjectEditor")[1].split("async function saveProject")[0]
        self.assertIn("state.projects.find", chunk)
        self.assertIn("profile_missing", self.app_js)


if __name__ == "__main__":
    unittest.main()
