"""Tests for ``hermes_cli.stack`` (``hermes run|restart|stop``)."""

from __future__ import annotations

from pathlib import Path

import hermes_cli.stack as stack_mod


def test_resolve_chat_root_from_env(tmp_path, monkeypatch):
    chat = tmp_path / "hermes-chat"
    chat.mkdir()
    (chat / "server.py").write_text("# stub", encoding="utf-8")
    monkeypatch.setenv("HERMES_CHAT_ROOT", str(chat))
    assert stack_mod.resolve_chat_root() == chat.resolve()


def test_resolve_chat_root_none_when_env_invalid(monkeypatch):
    monkeypatch.setenv("HERMES_CHAT_ROOT", "/nonexistent/chat")
    assert stack_mod.resolve_chat_root() is None


def test_chat_env_path_when_present(tmp_path):
    chat = tmp_path / "hc"
    chat.mkdir()
    env = chat / "hermes-chat.env"
    env.write_text("HERMES_API_KEY=x\n", encoding="utf-8")
    assert stack_mod.chat_env_path(chat) == env


def test_read_chat_port_default(tmp_path, monkeypatch):
    monkeypatch.delenv("CHAT_PORT", raising=False)
    chat = tmp_path / "hc"
    chat.mkdir()
    assert stack_mod._read_chat_port(chat) == 3000


def test_read_chat_port_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("CHAT_PORT", raising=False)
    chat = tmp_path / "hc"
    chat.mkdir()
    (chat / "hermes-chat.env").write_text("CHAT_PORT=4000\n", encoding="utf-8")
    assert stack_mod._read_chat_port(chat) == 4000


def test_pids_listening_on_tcp_port_empty_when_ss_missing(monkeypatch):
    def _boom(*_a, **_k):
        raise FileNotFoundError()

    monkeypatch.setattr(stack_mod.subprocess, "run", _boom)
    assert stack_mod._pids_listening_on_tcp_port(3000) == []
