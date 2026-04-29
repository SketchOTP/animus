"""Tests for cron → Hermes Chat transcript delivery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cron import hermes_chat_delivery as hcd


def test_hermes_chat_data_dir_default(monkeypatch, tmp_path):
    monkeypatch.delenv("CHAT_DATA_DIR", raising=False)
    monkeypatch.delenv("HERMES_CHAT_DATA_DIR", raising=False)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    assert hcd.hermes_chat_data_dir() == (fake_home / ".hermes" / "chat").resolve()


def test_hermes_chat_data_dir_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path / "chatdata"))
    assert hcd.hermes_chat_data_dir() == (tmp_path / "chatdata").resolve()


def test_hermes_chat_data_dir_hermes_chat_env_alias(monkeypatch, tmp_path):
    monkeypatch.delenv("CHAT_DATA_DIR", raising=False)
    monkeypatch.setenv("HERMES_CHAT_DATA_DIR", str(tmp_path / "chatdata2"))
    assert hcd.hermes_chat_data_dir() == (tmp_path / "chatdata2").resolve()


def test_hermes_chat_data_dir_from_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("CHAT_DATA_DIR", raising=False)
    monkeypatch.delenv("HERMES_CHAT_DATA_DIR", raising=False)
    fake_home = tmp_path / "h"
    fake_home.mkdir()
    hermes_dir = fake_home / ".hermes"
    hermes_dir.mkdir()
    chatdir = tmp_path / "thechat"
    chatdir.mkdir()
    (hermes_dir / ".env").write_text(f"CHAT_DATA_DIR={chatdir}\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(fake_home))
    assert hcd.hermes_chat_data_dir() == chatdir.resolve()


def test_append_cron_project_creates_cron_thread(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    pid = "proj-uuid-1"
    hcd.append_cron_to_hermes_chat(
        kind="project",
        target_id=pid,
        text="Cronjob Response: test\n-------------\n\nHello",
        job_id="job1",
        job_name="nightly",
    )
    convs_path = tmp_path / "conversations.json"
    assert convs_path.is_file()
    convs = json.loads(convs_path.read_text(encoding="utf-8"))
    assert len(convs) == 1
    c0 = convs[0]
    assert c0["project_id"] == pid
    assert c0["title"] == hcd._CRON_CONV_TITLE
    assert len(c0["messages"]) == 1
    assert c0["messages"][0]["role"] == "assistant"
    assert c0["messages"][0].get("source") == "cron"
    assert c0["messages"][0].get("cron_job_id") == "job1"
    assert c0["messages"][0].get("cron_job_name") == "nightly"
    assert "Hello" in c0["messages"][0]["content"]

    hcd.append_cron_to_hermes_chat(
        kind="project",
        target_id=pid,
        text="Second run",
        job_id="job1",
        job_name="nightly",
    )
    convs2 = json.loads(convs_path.read_text(encoding="utf-8"))
    assert len(convs2) == 1
    assert len(convs2[0]["messages"]) == 2
    assert convs2[0]["messages"][1]["content"] == "Second run"
    assert convs2[0].get("notification_channel") == "cron"


def test_append_cron_project_uuid_case_merges_thread(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    pid_lower = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    convs = [
        {
            "id": "existing-cron-conv",
            "project_id": pid_lower,
            "session_id": "sess",
            "title": hcd._CRON_CONV_TITLE,
            "created_at": "2026-01-01T00:00:00Z",
            "messages": [],
        }
    ]
    (tmp_path / "conversations.json").write_text(
        json.dumps(convs, ensure_ascii=False), encoding="utf-8"
    )
    pid_upper = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"
    hcd.append_cron_to_hermes_chat(
        kind="project",
        target_id=pid_upper,
        text="From uppercase id",
        job_id="j",
        job_name="t",
    )
    out = json.loads((tmp_path / "conversations.json").read_text(encoding="utf-8"))
    assert len(out) == 1
    assert len(out[0]["messages"]) == 1
    assert out[0]["messages"][0]["content"] == "From uppercase id"


def test_append_cron_conversation(monkeypatch, tmp_path):
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    cid = "conv-aaa"
    convs = [
        {
            "id": cid,
            "project_id": None,
            "session_id": "sess",
            "title": "Main",
            "created_at": "2026-01-01T00:00:00Z",
            "messages": [{"role": "user", "content": "hi"}],
        }
    ]
    (tmp_path / "conversations.json").write_text(
        json.dumps(convs, ensure_ascii=False), encoding="utf-8"
    )
    hcd.append_cron_to_hermes_chat(
        kind="conversation",
        target_id=cid,
        text="Cron note",
        job_id="j",
        job_name="",
    )
    out = json.loads((tmp_path / "conversations.json").read_text(encoding="utf-8"))
    assert len(out[0]["messages"]) == 2
    assert out[0]["messages"][1]["content"] == "Cron note"
