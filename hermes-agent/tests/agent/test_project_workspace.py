"""Tests for ``agent.project_workspace``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_ensure_and_append_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    (tmp_path / "projects.json").write_text(
        json.dumps([{"id": "p1", "name": "T", "path": str(tmp_path / "proj")}]),
        encoding="utf-8",
    )
    root = tmp_path / "proj"
    root.mkdir()

    info = pw.ensure_workspace_files(root)
    assert (root / pw.HISTORY_FILENAME).is_file()
    assert (root / pw.STATUS_FILENAME).is_file()
    assert (root / pw.KNOWLEDGE_FILENAME).is_file()
    assert (root / pw.AGENTS_MD_FILENAME).is_file()
    assert (root / pw.CLAUDE_MD_FILENAME).is_file()
    assert (root / pw.CURSOR_RULES_FILENAME).is_file()
    assert "created" in info
    line = pw.append_project_history_line(root, "hello world", source="test")
    assert "— hello world" in line
    body = (root / pw.HISTORY_FILENAME).read_text(encoding="utf-8")
    assert "hello world" in body


def test_resolve_project_root_from_hermes_chat_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    proj = tmp_path / "myproj"
    proj.mkdir()
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    (tmp_path / "projects.json").write_text(
        json.dumps([{"id": "abc-123", "name": "Mine", "path": str(proj)}]),
        encoding="utf-8",
    )
    got = pw.resolve_project_root_from_hermes_chat_id("abc-123")
    assert got == proj.resolve()


def test_resolve_project_root_prefers_workspace_files_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    shallow = tmp_path / "Projects" / "kuki"
    real_root = tmp_path / "mnt" / "kuki-companion"
    shallow.mkdir(parents=True)
    real_root.mkdir(parents=True)
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    (tmp_path / "projects.json").write_text(
        json.dumps(
            [
                {
                    "id": "p-1",
                    "name": "kuki",
                    "path": str(shallow),
                    "workspace_files_path": str(real_root),
                }
            ]
        ),
        encoding="utf-8",
    )
    by_id = pw.read_hermes_chat_project_paths_by_id()
    assert by_id["p-1"] == str(real_root)
    got = pw.resolve_project_root_from_hermes_chat_id("p-1")
    assert got == real_root.resolve()


def test_resolve_project_root_uuid_case_insensitive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    proj = tmp_path / "myproj"
    proj.mkdir()
    pid_lower = "a1b2c3d4-e5f6-4789-a012-b3c4d5e6f708"
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    (tmp_path / "projects.json").write_text(
        json.dumps([{"id": pid_lower, "name": "Mine", "path": str(proj)}]),
        encoding="utf-8",
    )
    got = pw.resolve_project_root_from_hermes_chat_id(pid_lower.upper())
    assert got == proj.resolve()


def test_append_gateway_tool_history_line(tmp_path: Path) -> None:
    from agent import project_workspace as pw

    root = tmp_path / "g"
    root.mkdir()
    pw.ensure_workspace_files(root, generate_repo_map_if_missing=False)
    line = pw.append_gateway_tool_history_line(
        root, "read_file", {"path": "x.py"}, "file contents here", source="gateway"
    )
    assert "read_file" in line
    body = (root / pw.HISTORY_FILENAME).read_text(encoding="utf-8")
    assert "read_file" in body


def test_read_workspace_file_ensure_creates_files(tmp_path: Path) -> None:
    from agent import project_workspace as pw

    root = tmp_path / "rw"
    root.mkdir()
    (root / "main.py").write_text("x = 1\n", encoding="utf-8")
    assert not (root / pw.HISTORY_FILENAME).exists()
    assert not (root / pw.REPO_MAP_FILENAME).exists()
    hist = pw.read_workspace_file(root, "project_history", ensure=True)
    assert "# Project history" in hist
    m = pw.read_workspace_file(root, "repo_map", ensure=True)
    assert "main.py" in m
    assert (root / pw.HISTORY_FILENAME).is_file()
    assert (root / pw.REPO_MAP_FILENAME).is_file()


def test_refresh_repo_map_writes_file(tmp_path: Path) -> None:
    from agent import project_workspace as pw

    root = tmp_path / "r"
    root.mkdir()
    (root / "a.py").write_text("# hi\n", encoding="utf-8")
    sub = root / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("body\n", encoding="utf-8")
    info = pw.refresh_repo_map(root)
    assert info["file"] == pw.REPO_MAP_FILENAME
    text = (root / pw.REPO_MAP_FILENAME).read_text(encoding="utf-8")
    assert "a.py" in text
    assert "sub/b.txt" in text


def test_refresh_repo_map_ensures_and_mirrors_policy_files(tmp_path: Path) -> None:
    from agent import project_workspace as pw

    root = tmp_path / "proj"
    root.mkdir()
    (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
    canonical = "# Canonical agent rules\n- mirrored on refresh\n"
    (root / pw.AGENTS_MD_FILENAME).write_text(canonical, encoding="utf-8")
    (root / pw.CLAUDE_MD_FILENAME).write_text("# stale\n", encoding="utf-8")
    (root / pw.CURSOR_RULES_FILENAME).write_text("# stale\n", encoding="utf-8")
    (root / pw.STATUS_FILENAME).unlink(missing_ok=True)
    (root / pw.KNOWLEDGE_FILENAME).unlink(missing_ok=True)

    info = pw.refresh_repo_map(root)
    assert info["file"] == pw.REPO_MAP_FILENAME
    assert str(root / pw.STATUS_FILENAME) in info.get("created", [])
    assert str(root / pw.KNOWLEDGE_FILENAME) in info.get("created", [])
    assert str(root / pw.CLAUDE_MD_FILENAME) in info.get("updated", [])
    assert str(root / pw.CURSOR_RULES_FILENAME) in info.get("updated", [])
    assert (root / pw.CLAUDE_MD_FILENAME).read_text(encoding="utf-8") == canonical
    assert (root / pw.CURSOR_RULES_FILENAME).read_text(encoding="utf-8") == canonical


def test_iter_hermes_chat_project_roots_dedupes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    (tmp_path / "projects.json").write_text(
        json.dumps(
            [
                {"id": "1", "name": "A", "path": str(a)},
                {"id": "2", "name": "B", "path": str(b)},
                {"id": "3", "name": "A2", "path": str(a)},
            ]
        ),
        encoding="utf-8",
    )
    got = pw.iter_hermes_chat_project_roots()
    assert len(got) == 2
    assert a.resolve() in got and b.resolve() in got


def test_refresh_all_skips_sync_root_and_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent import project_workspace as pw

    sync = tmp_path / "SyncProjects"
    ghost = sync / "ghost"
    sync.mkdir()
    ghost.mkdir()
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HERMES_CHAT_PROJECTS_SYNC_ROOT", str(sync))
    (tmp_path / "projects.json").write_text(
        json.dumps(
            [
                {"id": "g", "name": "ghost", "path": str(ghost)},
                {"id": "s", "name": "bad", "path": str(sync)},
                {"id": "p", "name": "bad2", "path": str(tmp_path)},
            ]
        ),
        encoding="utf-8",
    )
    (ghost / "x.py").write_text("1\n", encoding="utf-8")
    rows = pw.refresh_all_hermes_chat_repo_maps()
    by_path = {r["path"]: r for r in rows}
    g = by_path[str(ghost.resolve())]
    assert g.get("repo_map_refreshed") is True
    assert g.get("file") == pw.REPO_MAP_FILENAME
    assert (ghost / pw.HISTORY_FILENAME).is_file()
    assert (ghost / pw.REPO_MAP_FILENAME).is_file()
    assert by_path[str(sync.resolve())]["skipped"] == "unsafe_workspace"
    assert by_path[str(tmp_path.resolve())]["skipped"] == "unsafe_workspace"


def test_refresh_all_missing_only_does_not_overwrite_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent import project_workspace as pw

    sync = tmp_path / "sp"
    p = sync / "proj"
    sync.mkdir()
    p.mkdir()
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HERMES_CHAT_PROJECTS_SYNC_ROOT", str(sync))
    (tmp_path / "projects.json").write_text(
        json.dumps([{"id": "1", "name": "P", "path": str(p)}]),
        encoding="utf-8",
    )
    pw.refresh_repo_map(p)
    (p / pw.REPO_MAP_FILENAME).write_text(
        (p / pw.REPO_MAP_FILENAME).read_text(encoding="utf-8") + "\n<!-- MARK -->\n",
        encoding="utf-8",
    )
    rows = pw.refresh_all_hermes_chat_repo_maps(missing_only=True)
    assert len(rows) == 1
    assert rows[0]["repo_map_refreshed"] is False
    assert "<!-- MARK -->" in (p / pw.REPO_MAP_FILENAME).read_text(encoding="utf-8")


def test_ensure_workspace_copies_setup_repo_and_appends_agent_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent import project_workspace as pw

    tmpl = tmp_path / "setup_repo.md"
    tmpl.write_text("# Bootstrap guide\n\nDo the thing.\n", encoding="utf-8")
    monkeypatch.setenv(pw.HERMES_CHAT_SETUP_REPO_MD_ENV, str(tmpl))
    root = tmp_path / "proj"
    root.mkdir()

    info = pw.ensure_workspace_files(root, generate_repo_map_if_missing=False)
    assert (root / pw.SETUP_REPO_FILENAME).is_file()
    assert str(root / pw.SETUP_REPO_FILENAME) in info.get("created", [])
    notes = (root / pw.NOTES_FILENAME).read_text(encoding="utf-8")
    assert "hermes-chat-setup-repo-bootstrap" not in notes
    assert (root / pw.AGENTS_MD_FILENAME).is_file()
    assert (root / pw.CLAUDE_MD_FILENAME).is_file()
    assert (root / pw.CURSOR_RULES_FILENAME).is_file()
    assert "Bootstrap guide" in (root / pw.SETUP_REPO_FILENAME).read_text(encoding="utf-8")


def test_ensure_workspace_skips_agent_note_when_agents_md_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent import project_workspace as pw

    tmpl = tmp_path / "setup_repo.md"
    tmpl.write_text("# Guide\n", encoding="utf-8")
    monkeypatch.setenv(pw.HERMES_CHAT_SETUP_REPO_MD_ENV, str(tmpl))
    root = tmp_path / "proj"
    root.mkdir()
    (root / pw.AGENTS_MD_FILENAME).write_text("# ok\n", encoding="utf-8")

    pw.ensure_workspace_files(root, generate_repo_map_if_missing=False)
    notes = (root / pw.NOTES_FILENAME).read_text(encoding="utf-8")
    assert "hermes-chat-setup-repo-bootstrap" not in notes


def test_policy_files_mirror_agents_md(tmp_path: Path) -> None:
    from agent import project_workspace as pw

    root = tmp_path / "proj"
    root.mkdir()
    canonical = "# Canonical agent rules\n- keep mirrored\n"
    (root / pw.AGENTS_MD_FILENAME).write_text(canonical, encoding="utf-8")
    (root / pw.CLAUDE_MD_FILENAME).write_text("# old\n", encoding="utf-8")
    (root / pw.CURSOR_RULES_FILENAME).write_text("# stale\n", encoding="utf-8")

    info = pw.ensure_workspace_files(root, generate_repo_map_if_missing=False)
    assert str(root / pw.CLAUDE_MD_FILENAME) in info.get("updated", [])
    assert str(root / pw.CURSOR_RULES_FILENAME) in info.get("updated", [])
    assert (root / pw.CLAUDE_MD_FILENAME).read_text(encoding="utf-8") == canonical
    assert (root / pw.CURSOR_RULES_FILENAME).read_text(encoding="utf-8") == canonical


def test_refresh_all_missing_only_creates_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent import project_workspace as pw

    sync = tmp_path / "sp"
    p = sync / "proj"
    sync.mkdir()
    p.mkdir()
    monkeypatch.setenv("CHAT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("HERMES_CHAT_PROJECTS_SYNC_ROOT", str(sync))
    (tmp_path / "projects.json").write_text(
        json.dumps([{"id": "1", "name": "P", "path": str(p)}]),
        encoding="utf-8",
    )
    pw.refresh_repo_map(p)
    (p / pw.HISTORY_FILENAME).unlink(missing_ok=True)
    rows = pw.refresh_all_hermes_chat_repo_maps(missing_only=True)
    assert rows[0]["repo_map_refreshed"] is False
    assert any(pw.HISTORY_FILENAME in c for c in rows[0].get("created", []))
    assert (p / pw.HISTORY_FILENAME).is_file()
