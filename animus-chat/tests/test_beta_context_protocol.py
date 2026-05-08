from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock
import json
import asyncio


class TestAnimusClientConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._env = mock.patch.dict("os.environ", {"CHAT_DATA_DIR": self._tdir.name}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)
        import server  # late import so CHAT_DATA_DIR is patched
        self.server = server
        self.server.DATA_DIR = Path(self._tdir.name)

    def test_get_client_config_omits_removed_beta_settings(self) -> None:
        payload = json.loads(
            asyncio.run(
                self.server.animus_client_config_get(None)
            ).body.decode("utf-8")
        )
        self.assertNotIn("beta", payload)
        self.assertNotIn("beta", payload.get("ui_settings") or {})

    def test_client_config_background_run_defaults_and_post(self) -> None:
        payload = json.loads(
            asyncio.run(
                self.server.animus_client_config_get(None)
            ).body.decode("utf-8")
        )
        self.assertIn("background_run", payload)
        self.assertFalse(payload["background_run"])

        class _Req:
            def __init__(self, body):
                self._body = body

            async def json(self):
                return self._body

        asyncio.run(self.server.animus_client_config_post(_Req({"background_run": True})))
        payload2 = json.loads(
            asyncio.run(
                self.server.animus_client_config_get(None)
            ).body.decode("utf-8")
        )
        self.assertTrue(payload2["background_run"])
        cfg = json.loads((Path(self._tdir.name) / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(cfg.get("background_run") is True)
        uis = cfg.get("animus_ui_settings") or {}
        self.assertTrue(uis.get("background_run_enabled") is True)

    def test_removed_beta_config_is_ignored_safely(self) -> None:
        cfg_path = Path(self._tdir.name) / "config.json"
        cfg_path.write_text(
            '{"wake_lock": false, "beta": {"skill_tool_context_protocol_enabled": true}, "animus_ui_settings": {"beta": {"auto_model_router_enabled": true}}}',
            encoding="utf-8",
        )
        payload = json.loads(
            asyncio.run(
                self.server.animus_client_config_get(None)
            ).body.decode("utf-8")
        )
        self.assertFalse(payload.get("background_run") is True)
        self.assertNotIn("beta", payload)
        self.assertNotIn("beta", payload.get("ui_settings") or {})

    def test_client_config_roundtrips_custom_skill_tool_presets(self) -> None:
        class _Req:
            def __init__(self, body):
                self._body = body

            async def json(self):
                return self._body

        body = {
            "ui_settings": {
                "skills_custom_profile": ["coding", "debug"],
                "skills_custom_enabled": True,
                "tools_custom_profile": ["read_file", "patch"],
                "tools_custom_enabled": False,
            }
        }
        asyncio.run(self.server.animus_client_config_post(_Req(body)))
        payload = json.loads(
            asyncio.run(
                self.server.animus_client_config_get(None)
            ).body.decode("utf-8")
        )
        ui = payload.get("ui_settings") or {}
        self.assertEqual(ui.get("skills_custom_profile"), ["coding", "debug"])
        self.assertTrue(ui.get("skills_custom_enabled"))
        self.assertEqual(ui.get("tools_custom_profile"), ["read_file", "patch"])
        self.assertFalse(ui.get("tools_custom_enabled"))


class TestRemovedBetaUiControls(unittest.TestCase):
    def test_ui_omits_skill_tool_context_protocol_controls(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "betaSkillToolEnabled",
            "betaSkillToolMode",
            "betaSelectorConfidence",
            "betaMaxSelectedTools",
            "betaMaxSelectedSkills",
            "betaDecisionDiagnosticsEnabled",
            "betaShadowBenchmarkPassed",
            "betaActiveLocalDevOnly",
        ):
            self.assertNotIn(marker, html)

    def test_ui_omits_auto_model_router_controls(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "betaAutoRouterEnabled",
            "betaRouterModelMode",
            "betaRouterProvider",
            "betaRouterModel",
            "betaFallbackToManual",
        ):
            self.assertNotIn(marker, html)

    def test_ui_has_background_stream_recovery_plumbing(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "scheduleBackgroundPhaseStreamRecovery",
            "isAnimusTabHiddenForBackgroundRun",
            "backgroundStreamRecoveryTimer",
        ):
            self.assertIn(marker, html)

    def test_ui_has_custom_skill_and_tool_profile_controls(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "app" / "index.html").read_text(encoding="utf-8")
        for marker in (
            "skillsCustomProfileBtn",
            "skillsCustomProfileToggle",
            "toolsCustomProfileBtn",
            "toolsCustomProfileToggle",
            "maybeSaveCustomPreset",
            "setCustomPresetEnabled",
        ):
            self.assertIn(marker, html)
