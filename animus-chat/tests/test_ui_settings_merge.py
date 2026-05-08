"""Server-side ``animus_ui_settings`` merge for client-config POST (Project Brief prefs)."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class UiSettingsCommandBriefMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._tdir, ignore_errors=True))
        self._data = Path(self._tdir) / "data"
        self._data.mkdir(parents=True)
        cfg = {
            "animus_ui_settings": {
                "commandBrief": {
                    "enabled": True,
                    "autoRefreshRecent": True,
                    "recentWindowDays": 7,
                },
                "wake_lock_enabled": True,
            }
        }
        (self._data / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        self._env = mock.patch.dict(os.environ, {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_post_without_command_brief_preserves_existing(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with TestClient(server.app) as client:
            r = client.post(
                "/api/animus/client-config",
                json={"ui_settings": {"background_run_enabled": False}},
            )
        self.assertEqual(r.status_code, 200, r.text)
        cfg = json.loads((self._data / "config.json").read_text(encoding="utf-8"))
        cb = (cfg.get("animus_ui_settings") or {}).get("commandBrief") or {}
        self.assertTrue(cb.get("enabled"))
        self.assertEqual(cb.get("recentWindowDays"), 7)

    def test_post_partial_command_brief_merges_fields(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with TestClient(server.app) as client:
            r = client.post(
                "/api/animus/client-config",
                json={"ui_settings": {"commandBrief": {"enabled": False}}},
            )
        self.assertEqual(r.status_code, 200, r.text)
        cfg = json.loads((self._data / "config.json").read_text(encoding="utf-8"))
        cb = (cfg.get("animus_ui_settings") or {}).get("commandBrief") or {}
        self.assertFalse(cb.get("enabled"))
        self.assertEqual(cb.get("recentWindowDays"), 7)
        self.assertTrue(cb.get("autoRefreshRecent"))


if __name__ == "__main__":
    unittest.main()
