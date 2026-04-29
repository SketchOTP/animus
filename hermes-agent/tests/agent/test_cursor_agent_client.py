"""Tests for Cursor CLI headless shim."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from agent.cursor_agent_client import CursorAgentClient, list_cursor_cli_models


class CursorAgentClientTests(unittest.TestCase):
    @patch("agent.cursor_agent_client.subprocess.Popen")
    def test_create_returns_tool_calls_when_marked_in_output(self, mock_popen):
        proc = Mock()
        proc.returncode = 0
        proc.communicate.return_value = (
            'Thought.\n<tool_call>{"id":"c1","type":"function","function":{"name":"read_file","arguments":"{}"}}</tool_call>',
            "",
        )
        mock_popen.return_value = proc

        client = CursorAgentClient(
            api_key="cursor-agent",
            base_url="cursor-agent://hermes",
            command="/bin/cursor-agent",
            args=["--print", "--output-format", "text", "--force"],
        )
        resp = client.chat.completions.create(
            model="auto",
            messages=[{"role": "user", "content": "hi"}],
        )
        self.assertEqual(resp.choices[0].finish_reason, "tool_calls")
        self.assertTrue(resp.choices[0].message.tool_calls)
        self.assertEqual(resp.choices[0].message.tool_calls[0].function.name, "read_file")

    @patch("agent.cursor_agent_client.shutil.which", return_value=None)
    def test_list_models_fallback_without_cli(self, _which):
        self.assertEqual(list_cursor_cli_models(), ["auto"])


if __name__ == "__main__":
    unittest.main()
