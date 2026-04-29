"""OpenAI-compatible shim that forwards Hermes turns to ``cursor-agent`` / ``cursor agent``.

Each ``chat.completions.create`` runs a short-lived subprocess: stdin carries the
serialized transcript (same layout as :mod:`agent.copilot_acp_client`), stdout
collects the printed reply. Tool calls are recovered from ``<tool_call>`` XML
blocks in the model text when the Cursor model follows the instructions.

Requires ``CURSOR_API_KEY`` in the environment (or Cursor's logged-in CLI auth
on the same machine). Configure the binary and flags with:

- ``HERMES_CURSOR_AGENT_COMMAND`` — default: first of ``cursor-agent``, ``cursor``
- ``HERMES_CURSOR_AGENT_ARGS`` — space-separated extra args before ``--model``
  (defaults include ``--print --output-format text --force``)
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from agent.copilot_acp_client import (
    _extract_tool_calls_from_text,
    _format_messages_as_prompt,
)

CURSOR_AGENT_MARKER_BASE_URL = "cursor-agent://hermes"
_DEFAULT_TIMEOUT_SECONDS = 900.0

_CURSOR_INTRO = [
    "You are the inference backend for Hermes Agent (terminal / gateway).",
    "Follow the user's instructions. When Hermes tools are required, you MUST emit "
    "tool calls using <tool_call>{...}</tool_call> blocks with JSON exactly in "
    "OpenAI function-call shape (id, type, function.name, function.arguments as a JSON string).",
    "If no tool is needed, answer normally.",
]


def _resolve_executable_and_base_args() -> tuple[str, list[str]]:
    """Return (argv0, base_args before --model …)."""
    override = (os.environ.get("HERMES_CURSOR_AGENT_COMMAND") or "").strip()
    raw_extra = (os.environ.get("HERMES_CURSOR_AGENT_ARGS") or "").strip()

    if override:
        exe = override
        if "/" not in override and "\\" not in override:
            found = shutil.which(override)
            if found:
                exe = found
        base = shlex.split(raw_extra) if raw_extra else []
        if not base:
            base_name = os.path.basename(exe).lower()
            if base_name == "cursor-agent":
                base = ["--print", "--output-format", "text", "--force"]
            else:
                base = ["agent", "--print", "--output-format", "text", "--force"]
        return exe, base

    for name in ("cursor-agent", "cursor"):
        found = shutil.which(name)
        if not found:
            continue
        if name == "cursor-agent":
            default = ["--print", "--output-format", "text", "--force"]
        else:
            default = ["agent", "--print", "--output-format", "text", "--force"]
        base = shlex.split(raw_extra) if raw_extra else default
        return found, base

    exe = "cursor-agent"
    base = shlex.split(raw_extra) if raw_extra else ["--print", "--output-format", "text", "--force"]
    return exe, base


def list_cursor_cli_models(*, timeout: float = 60.0) -> list[str]:
    """Return model ids from ``cursor-agent --list-models`` (best-effort parse)."""
    exe, _base = _resolve_executable_and_base_args()
    if shutil.which(exe) is None and "/" not in exe and "\\" not in exe:
        return ["auto"]

    base_name = os.path.basename(exe).lower()
    if base_name == "cursor":
        argv = [exe, "agent", "--list-models"]
    else:
        argv = [exe, "--list-models"]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"},
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ["auto"]

    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    models: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*[mKAH]", "", line).strip()
        if not line or line.lower().startswith("loading"):
            continue
        if line.lower() == "available models":
            continue
        m = re.match(r"^([a-z0-9][a-z0-9._-]*)\s+-\s+", line, re.I)
        if m:
            slug = m.group(1).strip()
            if slug and slug not in models:
                models.append(slug)
    return models if models else ["auto"]


class _CursorChatCompletions:
    def __init__(self, client: "CursorAgentClient"):
        self._client = client

    def create(self, **kwargs: Any) -> Any:
        return self._client._create_chat_completion(**kwargs)


class _CursorChatNamespace:
    def __init__(self, client: "CursorAgentClient"):
        self.completions = _CursorChatCompletions(client)


class CursorAgentClient:
    """Minimal OpenAI-client-compatible facade for Cursor CLI headless."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        command: str | None = None,
        args: list[str] | None = None,
        cursor_cwd: str | None = None,
        **_: Any,
    ):
        self.api_key = api_key or "cursor-agent"
        self.base_url = base_url or CURSOR_AGENT_MARKER_BASE_URL
        self._default_headers = dict(default_headers or {})
        if command:
            self._exe = command
            self._base_args = list(args or [])
        else:
            self._exe, self._base_args = _resolve_executable_and_base_args()
        self._cwd = str(Path(cursor_cwd or os.getcwd()).resolve())
        self.chat = _CursorChatNamespace(self)
        self.is_closed = False
        self._active_process: subprocess.Popen[str] | None = None
        self._active_process_lock = threading.Lock()

    def close(self) -> None:
        proc: subprocess.Popen[str] | None
        with self._active_process_lock:
            proc = self._active_process
            self._active_process = None
        self.is_closed = True
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    def _create_chat_completion(
        self,
        *,
        model: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        timeout: float | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: Any = None,
        **_: Any,
    ) -> Any:
        prompt_text = _format_messages_as_prompt(
            messages or [],
            model=model,
            tools=tools,
            tool_choice=tool_choice,
            intro_lines=_CURSOR_INTRO,
        )
        if timeout is None:
            effective_timeout = _DEFAULT_TIMEOUT_SECONDS
        elif isinstance(timeout, (int, float)):
            effective_timeout = float(timeout)
        else:
            _candidates = [
                getattr(timeout, attr, None)
                for attr in ("read", "write", "connect", "pool", "timeout")
            ]
            _numeric = [float(v) for v in _candidates if isinstance(v, (int, float))]
            effective_timeout = max(_numeric) if _numeric else _DEFAULT_TIMEOUT_SECONDS

        cursor_model = (model or "auto").strip() or "auto"
        argv = [self._exe] + self._base_args + ["--model", cursor_model]

        env = os.environ.copy()
        # api_key placeholder from resolver — real auth is env CURSOR_API_KEY
        if not env.get("CURSOR_API_KEY") and self.api_key and self.api_key != "cursor-agent":
            env["CURSOR_API_KEY"] = str(self.api_key)

        try:
            proc = subprocess.Popen(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._cwd,
                env=env,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Could not start Cursor CLI ({self._exe!r}). "
                "Install Cursor and ensure `cursor-agent` or `cursor` is on PATH, "
                "or set HERMES_CURSOR_AGENT_COMMAND."
            ) from exc

        with self._active_process_lock:
            self._active_process = proc
        self.is_closed = False

        try:
            out, err = proc.communicate(input=prompt_text + "\n", timeout=effective_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise TimeoutError(
                f"cursor-agent subprocess exceeded {effective_timeout:.0f}s timeout."
            ) from None
        finally:
            with self._active_process_lock:
                self._active_process = None
            self.is_closed = True

        if proc.returncode:
            detail = (err or "").strip() or (out or "").strip() or f"exit {proc.returncode}"
            raise RuntimeError(f"Cursor CLI exited with status {proc.returncode}: {detail[:2000]}")

        response_text = (out or "").strip()
        if not response_text and (err or "").strip():
            response_text = (err or "").strip()

        tool_calls, cleaned_text = _extract_tool_calls_from_text(response_text)
        usage = SimpleNamespace(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            prompt_tokens_details=SimpleNamespace(cached_tokens=0),
        )
        assistant_message = SimpleNamespace(
            content=cleaned_text,
            tool_calls=tool_calls,
            reasoning=None,
            reasoning_content=None,
            reasoning_details=None,
        )
        finish_reason = "tool_calls" if tool_calls else "stop"
        choice = SimpleNamespace(message=assistant_message, finish_reason=finish_reason)
        return SimpleNamespace(
            choices=[choice],
            usage=usage,
            model=cursor_model,
        )
