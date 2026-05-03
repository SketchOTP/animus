#!/usr/bin/env python3
"""Capture ANIMUS/Hermes prompt payloads for skills+tools toggle scenarios."""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request


SCENARIOS = [
    "all_skills_off",
    "all_tools_off",
    "some_skills_on",
    "some_tools_on",
    "all_skills_tools_on",
]

BARE_MIN_TOOLS = {
    "terminal",
    "read_file",
    "write_file",
    "patch",
    "search_files",
    "process",
    "execute_code",
    "delegate_task",
    "todo",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _req_json(method: str, url: str, payload: dict | None = None) -> tuple[int, object]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=45) as resp:
            raw = resp.read()
            if not raw:
                return int(resp.status), {}
            return int(resp.status), json.loads(raw.decode("utf-8", errors="replace"))
    except error.HTTPError as exc:
        raw = exc.read(4096).decode("utf-8", errors="replace")
        try:
            return int(exc.code or 0), json.loads(raw)
        except Exception:
            return int(exc.code or 0), {"error": raw}


def _skill_is_bare_minimum(skill: dict) -> bool:
    cat = str(skill.get("category") or "").strip().lower()
    if cat in {"software-development", "software development", "coding"}:
        return True
    if cat:
        return False
    text = (str(skill.get("name") or "") + " " + str(skill.get("description") or "")).lower()
    return any(k in text for k in ("code", "coding", "programming", "software"))


def _toggle_skill(base_url: str, name: str, enabled: bool) -> None:
    endpoint = "enable" if enabled else "disable"
    url = base_url.rstrip("/") + f"/api/skills/{endpoint}/" + parse.quote(name, safe="")
    st, body = _req_json("POST", url, {})
    if st >= 300 or not isinstance(body, dict) or not body.get("ok"):
        raise RuntimeError(f"Skill toggle failed for {name}: HTTP {st} {body}")


def _toggle_tool(base_url: str, name: str, enabled: bool) -> None:
    endpoint = "enable" if enabled else "disable"
    url = base_url.rstrip("/") + f"/api/tools/{endpoint}/" + parse.quote(name, safe="")
    st, body = _req_json("POST", url, {})
    if st >= 300 or not isinstance(body, dict) or not body.get("ok"):
        raise RuntimeError(f"Tool toggle failed for {name}: HTTP {st} {body}")


def _list_skills(base_url: str) -> list[dict]:
    st, body = _req_json("GET", base_url.rstrip("/") + "/api/skills/list")
    if st != 200 or not isinstance(body, list):
        raise RuntimeError(f"Could not list skills: HTTP {st} {body}")
    return [row for row in body if isinstance(row, dict)]


def _list_tools(base_url: str) -> list[dict]:
    st, body = _req_json("GET", base_url.rstrip("/") + "/api/tools/list")
    if st != 200 or not isinstance(body, dict) or not isinstance(body.get("tools"), list):
        raise RuntimeError(f"Could not list tools: HTTP {st} {body}")
    return [row for row in body["tools"] if isinstance(row, dict)]


def _apply_scenario(base_url: str, scenario: str) -> None:
    skills = _list_skills(base_url)
    tools = _list_tools(base_url)
    for s in skills:
        name = str(s.get("name") or s.get("id") or "").strip()
        if not name:
            continue
        if scenario == "all_skills_off":
            _toggle_skill(base_url, name, False)
        elif scenario == "some_skills_on":
            _toggle_skill(base_url, name, _skill_is_bare_minimum(s))
        else:
            _toggle_skill(base_url, name, True)

    for t in tools:
        name = str(t.get("name") or "").strip()
        if not name:
            continue
        if scenario == "all_tools_off":
            _toggle_tool(base_url, name, False)
        elif scenario == "some_tools_on":
            _toggle_tool(base_url, name, name in BARE_MIN_TOOLS)
        else:
            _toggle_tool(base_url, name, True)


def _chat_payload(scenario: str) -> dict:
    return {
        "model": "gpt-5.2-codex",
        "hermes_provider": "openai-codex",
        "stream": False,
        "max_tokens": 48,
        "conversation_id": f"matrix-{scenario}",
        "animus_skill_mode": True,
        "messages": [
            {"role": "system", "content": "Respond in one short sentence."},
            {
                "role": "user",
                "content": f"Capture scenario marker: {scenario}. Reply with exactly this marker.",
            },
        ],
    }


def _capture_internal_dump(
    *,
    chat_url: str,
    payload: dict,
    out_file: Path,
    dump_dirs: list[Path],
) -> None:
    before = {str(p) for d in dump_dirs for p in d.glob("request_dump_*.json")}
    st, body = _req_json("POST", chat_url, payload)
    if st >= 400:
        raise RuntimeError(f"Chat request failed: HTTP {st} {body}")
    deadline = time.time() + 12.0
    hit: Path | None = None
    while time.time() < deadline:
        candidates = [
            p
            for d in dump_dirs
            for p in d.glob("request_dump_*.json")
            if str(p) not in before
        ]
        if candidates:
            hit = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            break
        time.sleep(0.3)
    if hit is None:
        raise RuntimeError("No Hermes internal dump found. Ensure HERMES_DUMP_REQUESTS=1 on gateway.")
    shutil.copy2(hit, out_file)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "prompt_captures"
    out_dir.mkdir(parents=True, exist_ok=True)

    animus_base = (os.environ.get("ANIMUS_BASE_URL") or "http://127.0.0.1:3001").rstrip("/")
    chat_url = animus_base + "/api/chat"
    hermes_home = Path(os.environ.get("HERMES_HOME", str(repo_root / ".hermes"))).expanduser()
    dump_dirs = [hermes_home / "sessions", hermes_home / "logs"]
    for d in dump_dirs:
        d.mkdir(parents=True, exist_ok=True)

    for scenario in SCENARIOS:
        _apply_scenario(animus_base, scenario)
        payload = _chat_payload(scenario)
        animus_path = out_dir / f"animus_{scenario}.json"
        animus_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        internal_path = out_dir / f"hermes_internal_{scenario}.json"
        _capture_internal_dump(chat_url=chat_url, payload=payload, out_file=internal_path, dump_dirs=dump_dirs)
        meta = {
            "captured_at_utc": _now(),
            "scenario": scenario,
            "capture_scope": "skills_tools_matrix",
            "animus_payload_file": str(animus_path),
            "hermes_internal_file": str(internal_path),
        }
        internal_path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        print(str(internal_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
