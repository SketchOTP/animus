from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from animus.plugins.command_brief.cache_store import load_cache, save_cache  # noqa: E402
from animus.plugins.command_brief.constants import NO_RECENT_WORK_FOCUS  # noqa: E402
from animus.plugins.command_brief.daily_log import append_daily_summary, daily_log_path, read_daily_log  # noqa: E402
from animus.plugins.command_brief.governance import (  # noqa: E402
    GovernanceBundle,
    docs_changed_since,
    governance_fresh_for_command_brief_inference,
    read_governance_bundle,
    read_governance_stats,
)
from animus.plugins.command_brief.json_extract import extract_json_object  # noqa: E402
from animus.plugins.command_brief.regenerate import (  # noqa: E402
    classify_display_status,
    should_regenerate_auto,
)


class CommandBriefRegenerateTests(unittest.TestCase):
    def test_should_regenerate_auto_requires_all_flags(self) -> None:
        b = GovernanceBundle(
            workspace=Path("/tmp"),
            texts={},
            mtimes_iso={},
            max_mtime_epoch=1_000_000.0,
            errors=[],
        )
        now = 1_000_000.0 + 86400.0
        self.assertFalse(
            should_regenerate_auto(
                enabled=False,
                auto_refresh_recent=True,
                bundle=b,
                generated_at_iso="1970-01-01T00:00:00Z",
                recent_window_days=3,
                now_ts=now,
            )
        )
        self.assertFalse(
            should_regenerate_auto(
                enabled=True,
                auto_refresh_recent=False,
                bundle=b,
                generated_at_iso="1970-01-01T00:00:00Z",
                recent_window_days=3,
                now_ts=now,
            )
        )

    def test_inactive_no_auto_regenerate(self) -> None:
        old = 1_000_000.0
        b = GovernanceBundle(
            workspace=Path("/tmp"),
            texts={},
            mtimes_iso={},
            max_mtime_epoch=old,
            errors=[],
        )
        now = old + 10 * 86400.0
        self.assertFalse(
            should_regenerate_auto(
                enabled=True,
                auto_refresh_recent=True,
                bundle=b,
                generated_at_iso="2000-01-01T00:00:00Z",
                recent_window_days=3,
                now_ts=now,
            )
        )

    def test_classify_stale_outside_window(self) -> None:
        b = GovernanceBundle(
            workspace=Path("/tmp"),
            texts={},
            mtimes_iso={},
            max_mtime_epoch=1_000_000.0,
            errors=[],
        )
        st = classify_display_status(
            bundle=b,
            generated_at_iso="1970-01-01T00:00:00Z",
            recent_window_days=1,
            blocked=False,
            now_ts=1_000_000.0 + 5 * 86400.0,
        )
        self.assertEqual(st, "stale")


class CommandBriefGovernanceTests(unittest.TestCase):
    def test_only_approved_relative_paths_read(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "project_status.md").write_text("ok", encoding="utf-8")
            (root / "secret.txt").write_text("nope", encoding="utf-8")
            b = read_governance_bundle(root)
            self.assertIn("project_status.md", b.texts)
            self.assertNotIn("secret.txt", b.texts)

    def test_stats_has_no_texts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "repo_map.md").write_text("x", encoding="utf-8")
            s = read_governance_stats(root)
            self.assertEqual(s.texts, {})
            self.assertIsNotNone(s.max_mtime_epoch)

    def test_governance_fresh_for_inference_within_three_days(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "project_status.md").write_text("x", encoding="utf-8")
            s = read_governance_stats(root)
            self.assertTrue(governance_fresh_for_command_brief_inference(s))

    def test_governance_stale_for_inference_ancient_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "project_status.md").write_text("x", encoding="utf-8")
            os.utime(root / "project_status.md", (946684800.0, 946684800.0))
            s = read_governance_stats(root)
            self.assertFalse(governance_fresh_for_command_brief_inference(s))

    def test_docs_changed_since(self) -> None:
        b = GovernanceBundle(
            workspace=Path("/tmp"),
            texts={"project_status.md": "a"},
            mtimes_iso={},
            max_mtime_epoch=2_000.0,
            errors=[],
        )
        self.assertTrue(docs_changed_since(b, "1970-01-01T00:00:00Z"))
        self.assertFalse(docs_changed_since(b, "2038-01-01T00:00:00Z"))


class CommandBriefCacheLogTests(unittest.TestCase):
    def test_cache_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            save_cache(d, {"p1": {"projectId": "p1", "name": "A"}})
            data = load_cache(d)
            self.assertEqual(data["summaries"]["p1"]["name"], "A")

    def test_append_preserves_prior(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            append_daily_summary(
                root,
                model_label="openai/gpt-4o-mini",
                status="active",
                source_files=["project_status.md"],
                current_focus="test",
                recent_changes=["c1"],
                next_actions=["n1"],
                risks=["r1"],
            )
            first = read_daily_log(root)
            append_daily_summary(
                root,
                model_label="openai/gpt-4o-mini",
                status="inactive",
                source_files=["project_status.md"],
                current_focus="second",
                recent_changes=["c2"],
                next_actions=[],
                risks=[],
            )
            second = read_daily_log(root)
            self.assertIn("test", second)
            self.assertIn("second", second)
            self.assertGreater(len(second), len(first))


class CommandBriefJsonTests(unittest.TestCase):
    def test_extract_json_strips_fence(self) -> None:
        raw = """```json
{"status":"unknown","currentFocus":"x","recentChanges":[],"nextActions":[],"risks":[],"sourceFiles":["a.md"]}
```"""
        out = extract_json_object(raw)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out.get("status"), "unknown")

    def test_extract_json_preamble_and_brace_inside_string(self) -> None:
        raw = """Here is the summary.
{"status":"active","currentFocus":"literal } brace","recentChanges":[],"nextActions":[],"risks":[],"sourceFiles":["project_status.md"]}
Thanks."""
        out = extract_json_object(raw)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out.get("status"), "active")
        self.assertEqual(out.get("currentFocus"), "literal } brace")

    def test_extract_json_trailing_junk_after_object(self) -> None:
        raw = '{"status":"unknown","currentFocus":"x","recentChanges":[],"nextActions":[],"risks":[],"sourceFiles":[]}\n\n(notes)'
        out = extract_json_object(raw)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertEqual(out.get("currentFocus"), "x")


class CommandBriefSummarizeRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_400_on_json_mode_retries_plain_body(self) -> None:
        from animus.plugins.command_brief import summarize as sm

        order: list[bool] = []

        class FakeClient:
            async def __aenter__(self) -> FakeClient:
                return self

            async def __aexit__(self, *a: object) -> None:
                return None

            async def post(self, url: str, headers=None, json=None) -> object:
                payload = json or {}
                has_rf = "response_format" in payload
                order.append(has_rf)

                class R:
                    status_code = 400 if has_rf else 200

                    async def aread(self_inner) -> bytes:
                        if has_rf:
                            return b'{"error":"unsupported"}'
                        return __import__("json").dumps(
                            {
                                "choices": [
                                    {
                                        "message": {
                                            "content": '{"status":"unknown","currentFocus":"ok","recentChanges":[],"nextActions":[],"risks":[],"sourceFiles":[]}'
                                        }
                                    }
                                ]
                            }
                        ).encode("utf-8")

                return R()

        with mock.patch("httpx.AsyncClient", lambda *a, **kw: FakeClient()):
            bundle = GovernanceBundle(
                workspace=Path("/tmp"),
                texts={"project_status.md": "x"},
                mtimes_iso={},
                max_mtime_epoch=1.0,
                errors=[],
            )
            norm, _raw, _m = await sm.run_summary_completion(
                hermes_api="http://example.test",
                headers={},
                model="m",
                hermes_provider="openai",
                hermes_base_url="",
                bundle=bundle,
            )
        self.assertEqual(order, [True, False])
        self.assertIsNotNone(norm)
        assert norm is not None
        self.assertEqual(norm["currentFocus"], "ok")


class CommandBriefDailyLogRouteTests(unittest.TestCase):
    """GET /api/command-brief/daily-log materializes template when missing (no model)."""

    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._proj = Path(self._tdir.name) / "myrepo"
        self._proj.mkdir(parents=True)
        (self._proj / "project_status.md").write_text("ok", encoding="utf-8")
        self._data = Path(self._tdir.name) / "data"
        self._data.mkdir(parents=True)
        (self._data / "config.json").write_text("{}", encoding="utf-8")
        (self._data / "projects.json").write_text(
            json.dumps([{"id": "cb-dl-1", "name": "DL", "path": str(self._proj)}]),
            encoding="utf-8",
        )
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_daily_log_creates_file_when_missing(self) -> None:
        import server

        server.DATA_DIR = self._data
        log_path = daily_log_path(self._proj)
        self.assertFalse(log_path.is_file())
        from starlette.testclient import TestClient

        with TestClient(server.app) as client:
            r = client.get("/api/command-brief/daily-log?" + f"path={self._proj}")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(log_path.is_file())
        body = r.json()
        self.assertIn("# Project Daily Summaries", body.get("content", ""))
        self.assertIn("Animus Command Brief", body.get("content", ""))

    def test_daily_log_does_not_overwrite_existing(self) -> None:
        import server

        server.DATA_DIR = self._data
        existing = "# Custom prior\n\nkeep me\n"
        daily_log_path(self._proj).parent.mkdir(parents=True, exist_ok=True)
        daily_log_path(self._proj).write_text(existing, encoding="utf-8")
        from starlette.testclient import TestClient

        with TestClient(server.app) as client:
            r = client.get("/api/command-brief/daily-log?" + f"path={self._proj}")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(daily_log_path(self._proj).read_text(encoding="utf-8"), existing)
        self.assertEqual(r.json().get("content"), existing)


class CommandBriefSyncAutoSingleProjectTests(unittest.TestCase):
    """Auto sync runs summarizer only for projects that pass should_regenerate_auto."""

    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._data = Path(self._tdir.name) / "data"
        self._data.mkdir(parents=True)
        base = Path(self._tdir.name) / "repos"
        self._p1 = base / "recent"
        self._p2 = base / "stale_time"
        self._p3 = base / "stale_time2"
        for p in (self._p1, self._p2, self._p3):
            p.mkdir(parents=True)
            (p / "project_status.md").write_text("governance", encoding="utf-8")
        # Far-past mtimes so governance is unambiguously outside the recent window (not ~40d).
        ancient = 946684800.0  # 2000-01-01 UTC
        os.utime(self._p2 / "project_status.md", (ancient, ancient))
        os.utime(self._p3 / "project_status.md", (ancient, ancient))
        (self._data / "config.json").write_text(
            json.dumps(
                {
                    "animus_ui_settings": {
                        "commandBrief": {
                            "enabled": True,
                            "autoRefreshRecent": True,
                            "recentWindowDays": 3,
                        }
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (self._data / "projects.json").write_text(
            json.dumps(
                [
                    {"id": "cb-a1", "name": "Recent", "path": str(self._p1)},
                    {"id": "cb-a2", "name": "Old", "path": str(self._p2)},
                    {"id": "cb-a3", "name": "Old2", "path": str(self._p3)},
                ]
            ),
            encoding="utf-8",
        )
        summaries = {
            "cb-a1": {
                "projectId": "cb-a1",
                "name": "Recent",
                "status": "active",
                "generatedAt": "2000-01-01T00:00:00Z",
                "currentFocus": "MARK_CB_A1",
                "recentChanges": [],
                "nextActions": [],
                "risks": [],
                "sourceFiles": [],
            },
            "cb-a2": {
                "projectId": "cb-a2",
                "name": "Old",
                "status": "inactive",
                "generatedAt": "2000-01-01T00:00:00Z",
                "currentFocus": "MARK_CB_A2",
                "recentChanges": [],
                "nextActions": [],
                "risks": [],
                "sourceFiles": [],
            },
            "cb-a3": {
                "projectId": "cb-a3",
                "name": "Old2",
                "status": "inactive",
                "generatedAt": "2000-01-01T00:00:00Z",
                "currentFocus": "MARK_CB_A3",
                "recentChanges": [],
                "nextActions": [],
                "risks": [],
                "sourceFiles": [],
            },
        }
        save_cache(self._data, summaries)
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_auto_sync_calls_summarizer_once(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        workspaces: list[Path] = []

        async def fake_run_summary(**kwargs: object) -> tuple[dict[str, object], str, str]:
            b = kwargs.get("bundle")
            assert hasattr(b, "workspace")
            workspaces.append(b.workspace)
            return (
                {
                    "status": "active",
                    "currentFocus": "regenerated_focus",
                    "recentChanges": ["c"],
                    "nextActions": ["n"],
                    "risks": [],
                    "sourceFiles": ["project_status.md"],
                },
                "{}",
                "m",
            )

        with mock.patch.object(
            server,
            "ensure_animus_general_project",
            lambda: None,
        ), mock.patch(
            "animus.plugins.command_brief.routes.run_summary_completion",
            side_effect=fake_run_summary,
        ), mock.patch("hermes_runner.gateway_upstream_headers", return_value={}):
            with TestClient(server.app) as client:
                r = client.post(
                    "/api/command-brief/sync",
                    json={
                        "mode": "auto",
                        "inference": {
                            "model": "gpt-4o-mini",
                            "hermes_provider": "openai",
                        },
                    },
                )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(workspaces), 1)
        self.assertEqual(workspaces[0].resolve(), self._p1.resolve())
        data = load_cache(self._data)
        summ = data["summaries"]
        self.assertEqual(summ["cb-a1"].get("currentFocus"), "regenerated_focus")
        self.assertEqual(summ["cb-a2"].get("currentFocus"), NO_RECENT_WORK_FOCUS)
        self.assertEqual(summ["cb-a3"].get("currentFocus"), NO_RECENT_WORK_FOCUS)
        log_text = daily_log_path(self._p1).read_text(encoding="utf-8")
        self.assertIn("regenerated_focus", log_text)
        self.assertFalse(daily_log_path(self._p2).is_file())
        self.assertFalse(daily_log_path(self._p3).is_file())


class CommandBriefManualSyncSkipsStaleInferenceTests(unittest.TestCase):
    """Manual refresh must not call Hermes when governance is older than INFERENCE_RECENT_DAYS."""

    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._data = Path(self._tdir.name) / "data"
        self._data.mkdir(parents=True)
        self._proj = Path(self._tdir.name) / "stale_repo"
        self._proj.mkdir(parents=True)
        (self._proj / "project_status.md").write_text("x", encoding="utf-8")
        ancient = 946684800.0
        os.utime(self._proj / "project_status.md", (ancient, ancient))
        (self._data / "config.json").write_text(
            json.dumps(
                {
                    "animus_ui_settings": {
                        "commandBrief": {
                            "enabled": True,
                            "autoRefreshRecent": True,
                            "recentWindowDays": 14,
                        }
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (self._data / "projects.json").write_text(
            json.dumps([{"id": "cb-manual-1", "name": "Stale", "path": str(self._proj)}]),
            encoding="utf-8",
        )
        save_cache(
            self._data,
            {
                "cb-manual-1": {
                    "projectId": "cb-manual-1",
                    "name": "Stale",
                    "generatedAt": "2000-01-01T00:00:00Z",
                    "currentFocus": "OLD_FOCUS",
                    "recentChanges": ["keep"],
                    "nextActions": [],
                    "risks": [],
                    "sourceFiles": [],
                }
            },
        )
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_mode_one_skips_summarizer_when_governance_stale(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        calls: list[object] = []

        async def fake_run_summary(**kwargs: object) -> tuple[dict[str, object], str, str]:
            calls.append(True)
            return ({}, "", "m")

        with mock.patch.object(server, "ensure_animus_general_project", lambda: None), mock.patch(
            "animus.plugins.command_brief.routes.run_summary_completion",
            side_effect=fake_run_summary,
        ), mock.patch("hermes_runner.gateway_upstream_headers", return_value={}):
            with TestClient(server.app) as client:
                r = client.post(
                    "/api/command-brief/sync",
                    json={
                        "mode": "one",
                        "project_id": "cb-manual-1",
                        "inference": {"model": "gpt-4o-mini", "hermes_provider": "openai"},
                    },
                )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(calls, [])
        summ = load_cache(self._data)["summaries"]["cb-manual-1"]
        self.assertEqual(summ.get("currentFocus"), NO_RECENT_WORK_FOCUS)
        self.assertEqual(summ.get("recentChanges"), [])


class CommandBriefClientConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": self._tdir.name}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)
        import server

        self.server = server
        self.server.DATA_DIR = Path(self._tdir.name)

    def test_client_config_includes_command_brief_defaults(self) -> None:
        payload = json.loads(asyncio.run(self.server.animus_client_config_get(None)).body.decode("utf-8"))
        self.assertIn("command_brief", payload)
        self.assertFalse(payload["command_brief"]["enabled"])
        self.assertTrue(payload["command_brief"]["autoRefreshRecent"])
        self.assertEqual(payload["command_brief"]["recentWindowDays"], 3)


class CommandBriefSyncErrorResponseTests(unittest.TestCase):
    """Regression: Starlette JSONResponse uses status_code=, not status=."""

    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": self._tdir.name}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)
        import server

        self.server = server
        self.server.DATA_DIR = Path(self._tdir.name)
        (Path(self._tdir.name) / "config.json").write_text(
            json.dumps(
                {
                    "animus_ui_settings": {
                        "commandBrief": {
                            "enabled": False,
                            "autoRefreshRecent": True,
                            "recentWindowDays": 3,
                        }
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_sync_disabled_returns_400_json(self) -> None:
        from starlette.testclient import TestClient

        with TestClient(self.server.app) as client:
            r = client.post(
                "/api/command-brief/sync",
                json={
                    "mode": "auto",
                    "inference": {"model": "gpt-4o-mini", "hermes_provider": "openai"},
                },
            )
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json().get("error"), "command_brief_disabled")

    def test_sync_missing_inference_returns_400_json(self) -> None:
        (Path(self._tdir.name) / "config.json").write_text(
            json.dumps(
                {
                    "animus_ui_settings": {
                        "commandBrief": {
                            "enabled": True,
                            "autoRefreshRecent": True,
                            "recentWindowDays": 3,
                        }
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        from starlette.testclient import TestClient

        with TestClient(self.server.app) as client:
            r = client.post("/api/command-brief/sync", json={"mode": "auto", "inference": {}})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn("inference", r.json().get("error", ""))


class CommandBriefSyncAutoRefreshOffTests(unittest.TestCase):
    """POST sync mode=auto with autoRefreshRecent false must not require inference (read-only snapshot)."""

    def setUp(self) -> None:
        self._tdir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._tdir, ignore_errors=True))
        self._data = Path(self._tdir) / "data"
        self._data.mkdir(parents=True)
        (self._data / "config.json").write_text(
            json.dumps(
                {
                    "animus_ui_settings": {
                        "commandBrief": {
                            "enabled": True,
                            "autoRefreshRecent": False,
                            "recentWindowDays": 3,
                        }
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (self._data / "projects.json").write_text(json.dumps([]), encoding="utf-8")
        save_cache(self._data, {})
        self._env = mock.patch.dict(os.environ, {"CHAT_DATA_DIR": str(self._data)}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_auto_sync_without_inference_returns_ok(self) -> None:
        import server

        from starlette.testclient import TestClient

        server.DATA_DIR = self._data
        with TestClient(server.app) as client:
            r = client.post("/api/command-brief/sync", json={"mode": "auto"})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("errors"), [])
        self.assertIsInstance(body.get("summaries"), list)


class CommandBriefUiSmokeTests(unittest.TestCase):
    def test_index_has_command_brief_markers(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "commandBriefOverlay",
            "commandBriefCloseBtn",
            "commandBriefSettingsCollapseHead",
            "settingsCommandBriefGroup",
            "projOpenSummaries",
            "commandBriefInferencePayload",
            "/api/command-brief/state",
            "/api/command-brief/health",
            "commandBriefPluginStatusText",
            "command_brief_plugin",
            "Project Brief",
        ):
            self.assertIn(marker, html)

    def test_startup_gates_command_brief_api_behind_enabled_pref(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        self.assertIn("isCommandBriefFeatureWanted()", html)
        self.assertIn("getCommandBriefPrefs().enabled", html)
        self.assertIn("loadCommandBriefBootstrap", html)
        gate_idx = html.find("if (isCommandBriefFeatureWanted() && getCommandBriefPrefs().enabled)")
        boot_idx = html.find("loadCommandBriefBootstrap", gate_idx)
        self.assertGreater(boot_idx, gate_idx)
        self.assertLess(boot_idx - gate_idx, 900, "loadCommandBriefBootstrap should sit near the enabled gate")
        chunk = html[gate_idx : gate_idx + 500]
        self.assertIn("isDesktopSidebarRail()", chunk)
        self.assertIn("setCommandBriefOverlayVisible(true)", chunk)


class CommandBriefHealthEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": self._tdir.name}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_health_available_when_routes_loaded(self) -> None:
        import server

        server.DATA_DIR = Path(self._tdir.name)
        from starlette.testclient import TestClient

        with TestClient(server.app) as client:
            r = client.get("/api/command-brief/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body.get("plugin"), "command_brief")
        self.assertTrue(body.get("available"))
        self.assertTrue(body.get("routes_registered"))
        self.assertNotIn("reason", body)

    def test_health_unavailable_when_routes_empty(self) -> None:
        import server

        server.DATA_DIR = Path(self._tdir.name)
        from starlette.testclient import TestClient

        with mock.patch.object(server, "_COMMAND_BRIEF_ROUTES", []), mock.patch.object(
            server, "_COMMAND_BRIEF_IMPORT_ERROR", "simulated missing plugin"
        ):
            with TestClient(server.app) as client:
                r = client.get("/api/command-brief/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertFalse(body.get("available"))
        self.assertFalse(body.get("routes_registered"))
        self.assertEqual(body.get("reason"), "simulated missing plugin")

    def test_client_config_includes_plugin_field(self) -> None:
        import server

        server.DATA_DIR = Path(self._tdir.name)
        payload = json.loads(asyncio.run(server.animus_client_config_get(None)).body.decode("utf-8"))
        self.assertIn("command_brief_plugin", payload)
        self.assertIn("available", payload["command_brief_plugin"])
        self.assertIsInstance(payload["command_brief_plugin"]["available"], bool)


class CommandBriefImportIsolationTests(unittest.TestCase):
    def test_server_imports_without_sibling_animus_package(self) -> None:
        """Buyer-style tree: animus-chat/ only (no ../animus) — server must import; Command Brief routes empty."""
        td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, td, ignore_errors=True)
        src_chat = ROOT / "animus-chat"
        dest_chat = td / "animus-chat"
        ignore = shutil.ignore_patterns("__pycache__", ".venv", "*.pyc", "data")
        shutil.copytree(src_chat, dest_chat, ignore=ignore)
        env = os.environ.copy()
        env["CHAT_DATA_DIR"] = str(td / "chatdata")
        Path(env["CHAT_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
        env["HERMES_AGENT_DIR"] = str(ROOT / "hermes-agent")
        # Parent test runners often set PYTHONPATH to the monorepo (includes `animus/`); clear so
        # this subprocess truly simulates animus-chat-only without sibling plugin package.
        env.pop("PYTHONPATH", None)
        code = (
            "import server\n"
            "assert not server._COMMAND_BRIEF_ROUTES, 'expected no command-brief routes without animus package'\n"
            "assert server._COMMAND_BRIEF_IMPORT_ERROR, 'expected import error recorded'\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(dest_chat),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)


if __name__ == "__main__":
    unittest.main()
