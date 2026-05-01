"""Regression tests for allowlisted ``animus_client`` slugs (token_usage.jsonl).

Run from ``animus-chat/``::

    python3 -m unittest tests.test_token_usage_animus_client -v

Uses ``CHAT_DATA_DIR`` pointing at a temp dir so the real ``~/.hermes`` tree is
not touched. Covers slug normalization, ``POST /api/tokens/record``, Help,
cron trigger, and cron prompt-optimizer paths (gateway calls mocked).
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.testclient import TestClient


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _make_request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode("latin-1"), v.encode("utf-8")) for k, v in headers.items()]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "path": "/api/tokens/record",
            "headers": raw,
            "client": ("127.0.0.1", 1234),
            "server": ("test", 80),
            "scheme": "http",
        }
    )


class TestAnimusClientSlugs(unittest.TestCase):
    def setUp(self) -> None:
        self._tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tdir.cleanup)
        self._env = mock.patch.dict(os.environ, {"CHAT_DATA_DIR": self._tdir.name}, clear=False)
        self._env.start()
        self.addCleanup(self._env.stop)

    def _usage_path(self) -> Path:
        return Path(self._tdir.name) / "token_usage.jsonl"

    def _last_row(self) -> dict:
        p = self._usage_path()
        self.assertTrue(p.is_file(), "token_usage.jsonl missing")
        lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertTrue(lines, "jsonl empty")
        row = json.loads(lines[-1])
        self.assertIsInstance(row, dict)
        return row

    def test_all_allowlisted_slugs_normalize_to_self(self) -> None:
        from token_usage import ANIMUS_CLIENT_SLUGS, normalize_animus_client_slug

        for slug in ANIMUS_CLIENT_SLUGS:
            self.assertEqual(normalize_animus_client_slug(slug), slug)
            self.assertEqual(normalize_animus_client_slug(slug.upper()), slug)

    def test_invalid_slugs_return_none(self) -> None:
        from token_usage import normalize_animus_client_slug

        for raw in (
            "random-test",
            "admin",
            "../../weird",
            "cursor",
            "chat-extra",
            "",
            "   ",
            "PLANX",
        ):
            self.assertIsNone(normalize_animus_client_slug(raw), repr(raw))

    def test_animus_client_from_request_header_casing(self) -> None:
        from token_usage import ANIMUS_CLIENT_HEADER, animus_client_from_request

        req = _make_request({ANIMUS_CLIENT_HEADER: "ChAt"})
        self.assertEqual(animus_client_from_request(req), "chat")

    def test_animus_client_from_request_blank(self) -> None:
        from token_usage import ANIMUS_CLIENT_HEADER, animus_client_from_request

        for v in ("", "  ", "\t"):
            req = _make_request({ANIMUS_CLIENT_HEADER: v})
            self.assertIsNone(animus_client_from_request(req))

    def test_record_token_usage_omits_animus_client_when_invalid(self) -> None:
        from token_usage import record_token_usage

        record_token_usage("openai", "gpt-4", 1, 2, "other", "", animus_client="admin")
        row = self._last_row()
        self.assertNotIn("animus_client", row)

    def test_record_token_usage_accepts_valid_slug(self) -> None:
        from token_usage import record_token_usage

        record_token_usage("openai", "gpt-4", 3, 4, "plan", "p1", animus_client="plan")
        row = self._last_row()
        self.assertEqual(row.get("animus_client"), "plan")

    def test_tokens_record_post_valid_headers(self) -> None:
        from token_usage import token_usage_route_table

        app = Starlette(routes=token_usage_route_table())
        client = TestClient(app)
        for slug in ("chat", "plan", "skills", "wizard", "web"):
            r = client.post(
                "/api/tokens/record",
                json={
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "source": "plan" if slug == "plan" else "chat",
                    "source_id": "test",
                    "input_tokens": 10,
                    "output_tokens": 2,
                },
                headers={"X-Animus-Client": slug},
            )
            self.assertEqual(r.status_code, 200, r.text)
            self.assertTrue(r.json().get("ok"))
        rows = [json.loads(ln) for ln in self._usage_path().read_text(encoding="utf-8").splitlines() if ln.strip()]
        by_slug = {r.get("animus_client"): r for r in rows if "animus_client" in r}
        self.assertEqual(set(by_slug), {"chat", "plan", "skills", "wizard", "web"})

    def test_tokens_record_post_invalid_header_no_arbitrary_slug(self) -> None:
        from token_usage import token_usage_route_table

        app = Starlette(routes=token_usage_route_table())
        client = TestClient(app)
        r = client.post(
            "/api/tokens/record",
            json={
                "provider": "x",
                "model": "y",
                "source": "chat",
                "input_tokens": 1,
                "output_tokens": 1,
            },
            headers={"X-Animus-Client": "random-test"},
        )
        self.assertEqual(r.status_code, 200)
        row = self._last_row()
        self.assertNotIn("animus_client", row)
        self.assertEqual(row.get("source"), "chat")

    def test_help_ask_post_records_animus_client_help(self) -> None:
        import help_routes

        class FakeResp:
            status_code = 200
            content = b"{}"
            text = ""

            def json(self) -> dict:
                return {
                    "choices": [{"message": {"content": "hello from guide"}}],
                    "model": "gpt-4o-mini",
                    "usage": {"prompt_tokens": 7, "completion_tokens": 3},
                }

        class FakeClient:
            def __init__(self, *a, **kw) -> None:
                pass

            async def __aenter__(self) -> FakeClient:
                return self

            async def __aexit__(self, *a) -> None:
                return None

            async def post(self, url: str, json=None, headers=None) -> FakeResp:
                return FakeResp()

        app = Starlette(routes=help_routes.help_route_table())
        with mock.patch.object(help_routes.httpx, "AsyncClient", FakeClient):
            client = TestClient(app)
            r = client.post(
                "/api/help/ask",
                json={
                    "question": "What is ANIMUS?",
                    "model": "gpt-4o-mini",
                    "hermes_provider": "openai",
                },
            )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body.get("ok"))
        row = self._last_row()
        self.assertEqual(row.get("animus_client"), "help")
        self.assertEqual(row.get("source"), "help")

    def test_cron_trigger_records_animus_client_cron(self) -> None:
        import cron_routes

        jid = "a" * 12

        async def fake_gw(method: str, path: str, json_body=None):
            if method == "POST" and path.endswith("/run"):
                return 200, {"job": {"id": jid, "provider": "openai", "model": "gpt-4o"}}
            if method == "GET" and f"/api/jobs/{jid}" in path:
                return 200, {"job": {"id": jid, "hermes_provider": "openai", "model": "gpt-4o"}}
            return 404, {}

        app = Starlette(routes=cron_routes.cron_route_table())
        with mock.patch.object(cron_routes, "_gw", fake_gw):
            client = TestClient(app)
            r = client.post(f"/api/cron/trigger/{jid}")
        self.assertEqual(r.status_code, 200, r.text)
        row = self._last_row()
        self.assertEqual(row.get("animus_client"), "cron")
        self.assertEqual(row.get("source"), "cron")
        self.assertEqual(row.get("source_id"), jid)

    def test_cron_optimize_prompt_records_prompt_optimizer(self) -> None:
        import cron_routes

        class FakeResp:
            status_code = 200
            content = b"{}"
            text = ""

            def json(self) -> dict:
                return {
                    "choices": [{"message": {"content": "rewritten prompt text"}}],
                    "model": "gpt-4o-mini",
                    "usage": {"prompt_tokens": 20, "completion_tokens": 5},
                }

        class FakeClient:
            def __init__(self, *a, **kw) -> None:
                pass

            async def __aenter__(self) -> FakeClient:
                return self

            async def __aexit__(self, *a) -> None:
                return None

            async def post(self, url: str, json=None, headers=None) -> FakeResp:
                return FakeResp()

        app = Starlette(routes=cron_routes.cron_route_table())
        with mock.patch.object(cron_routes.httpx, "AsyncClient", FakeClient):
            client = TestClient(app)
            r = client.post(
                "/api/cron/optimize-prompt",
                json={"prompt": "do the thing", "hermes_provider": "openai", "model": "gpt-4o-mini"},
            )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json().get("ok"))
        row = self._last_row()
        self.assertEqual(row.get("animus_client"), "prompt-optimizer")
        self.assertEqual(row.get("source"), "cron")
        self.assertEqual(row.get("source_id"), "optimize-prompt")

    def test_guide_file_present_for_help_tests(self) -> None:
        """Sanity: Help route tests require the monorepo user guide."""
        guide = _repo_root() / "docs" / "animus-user-guide.md"
        self.assertTrue(guide.is_file(), f"missing {guide}")

    def test_tokens_usage_get_full_returns_animus_client(self) -> None:
        """GET /api/tokens/usage?full=1 echoes JSONL animus_client on each record."""
        from token_usage import token_usage_route_table

        app = Starlette(routes=token_usage_route_table())
        client = TestClient(app)
        r = client.post(
            "/api/tokens/record",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "source": "chat",
                "source_id": "conv-1",
                "input_tokens": 5,
                "output_tokens": 1,
            },
            headers={"X-Animus-Client": "chat"},
        )
        self.assertEqual(r.status_code, 200)
        r2 = client.get("/api/tokens/usage?full=1&source=all")
        self.assertEqual(r2.status_code, 200)
        body = r2.json()
        self.assertTrue(body.get("full"))
        recs = body.get("records") or []
        self.assertTrue(recs)
        last = recs[-1]
        self.assertEqual(last.get("animus_client"), "chat")
        self.assertEqual(last.get("source"), "chat")

    def test_index_html_csv_and_ui_reference_animus_client(self) -> None:
        """Static: Tokens tab CSV header + recent-log UI tag animus_client (browser not executed)."""
        html_path = Path(__file__).resolve().parent.parent / "app" / "index.html"
        text = html_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("animus_client", text)
        self.assertIn(
            "ts_iso,ts_local_12h,date_local,provider,model,input_tokens,output_tokens,total_tokens,source,source_id,animus_client",
            text,
        )
        self.assertIn("ANIMUS:${esc(ac)}", text)
        self.assertIn("mergeServerTokenEntriesFull", text)
        self.assertIn('id="tokenUsageAnimusClientList"', text)
        self.assertIn("ANIMUS client (product surface)", text)
        self.assertIn("Uncategorized / missing", text)
        self.assertIn("token-usage-client-head", text)
        self.assertIn("aggregateAnimusClientTotals", text)
        self.assertIn("renderAnimusClientBreakdown", text)
        self.assertIn("By source (logging)", text)
        self.assertIn("TOKEN_USAGE_AUTO_REFRESH_MS", text)
        self.assertIn("startTokenUsageAutoRefresh", text)
        self.assertIn("token-usage-chart-details", text)
        self.assertIn('id="tokenUsageChartDetailsThisMonth"', text)
        self.assertIn('id="tokenUsageChartDetailsYear"', text)
        self.assertIn('id="tokenUsageChartDetailsAllMonths"', text)
        self.assertIn("scheduleTokenUsageChartReflow", text)


if __name__ == "__main__":
    unittest.main()
