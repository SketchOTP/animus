"""Hermes runtime routes — tui-rpc allowlist, curator, kanban proxy."""

from __future__ import annotations

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


class RuntimeRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._tdir, ignore_errors=True))
        self._data = Path(self._tdir) / "data"
        self._data.mkdir(parents=True)
        (self._data / "config.json").write_text("{}", encoding="utf-8")
        self._env = mock.patch.dict(os.environ, {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_tui_rpc_rejects_unknown_method(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with TestClient(server.app) as client:
            r = client.post(
                "/api/hermes/runtime/tui-rpc",
                json={"method": "rollback.list", "params": {}},
            )
        self.assertEqual(r.status_code, 403, r.text)

    def test_tui_rpc_allows_complete_slash(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        fake = {"jsonrpc": "2.0", "id": 1, "result": {"items": []}, "_rpc_ok": True}
        with mock.patch(
            "runtime_routes.dashboard_ws_json_rpc_call",
            new=mock.AsyncMock(return_value=(200, fake)),
        ):
            with TestClient(server.app) as client:
                r = client.post(
                    "/api/hermes/runtime/tui-rpc",
                    json={"method": "complete.slash", "params": {"text": "/"}},
                )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json().get("_rpc_ok"))

    def test_curator_status_ok(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        fake_state = {
            "paused": False,
            "run_count": 2,
            "last_run_at": "2026-05-01T00:00:00+00:00",
            "last_run_summary": "ok",
        }
        with mock.patch("agent.curator.load_state", return_value=fake_state), mock.patch(
            "agent.curator.is_enabled", return_value=True
        ):
            with TestClient(server.app) as client:
                r = client.get("/api/hermes/curator/status")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("status"), "enabled")

    def test_curator_run_invokes_cli(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with mock.patch(
            "runtime_routes.run_hermes",
            return_value={"ok": True, "stdout": "done", "stderr": "", "returncode": 0},
        ) as run:
            with TestClient(server.app) as client:
                r = client.post("/api/hermes/curator/run")
        self.assertEqual(r.status_code, 200, r.text)
        run.assert_called_once()
        self.assertEqual(run.call_args[0][0], ["curator", "run"])

    def test_kanban_proxy_requires_token(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with mock.patch("runtime_routes.hermes_dashboard_session_token", return_value=""):
            with TestClient(server.app) as client:
                r = client.get("/api/hermes/kanban/board")
        self.assertEqual(r.status_code, 401, r.text)

    def test_kanban_proxy_forwards_board(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        board = {"columns": {}, "tasks": []}
        with mock.patch("runtime_routes.hermes_dashboard_session_token", return_value="tok"), mock.patch(
            "runtime_routes.dashboard_http_json",
            new=mock.AsyncMock(return_value=(200, board)),
        ) as dash:
            with TestClient(server.app) as client:
                r = client.get("/api/hermes/kanban/board?board=default")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json(), board)
        dash.assert_called_once()
        self.assertIn("/api/plugins/kanban/board", dash.call_args[0][1])

    def test_kanban_proxy_rejects_write_path(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with mock.patch("runtime_routes.hermes_dashboard_session_token", return_value="tok"):
            with TestClient(server.app) as client:
                r = client.get("/api/hermes/kanban/tasks/abc123")
        self.assertEqual(r.status_code, 403, r.text)


if __name__ == "__main__":
    unittest.main()
