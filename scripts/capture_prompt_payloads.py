#!/usr/bin/env python3
"""Write ANIMUS -> Hermes chat payload captures for prompt review.

This script captures the upstream payload shape after ANIMUS-side skill-guidance
injection for four scenarios:
- skills enabled, first session turn
- skills enabled, follow-up turn
- skills disabled, first session turn
- skills disabled, follow-up turn
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

GUIDANCE = (
    "ANIMUS capability note: skill tools are available in this chat session. "
    "Reuse existing skills with skills_list/skill_view when relevant, and when a "
    "workflow repeats across requests, create or update a reusable skill with skill_manage."
)


def _build_messages(*, followup: bool, skills_enabled: bool) -> list[dict[str, str]]:
    if followup:
        messages = [
            {"role": "user", "content": "Give me a quick project status update."},
            {"role": "assistant", "content": "Status: services are aligned and config was normalized."},
            {
                "role": "user",
                "content": "Now list the remaining setup steps and risks in priority order.",
            },
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": "Give me a concise status summary and immediate next steps.",
            }
        ]
    if skills_enabled:
        messages.insert(0, {"role": "system", "content": GUIDANCE})
    return messages


def _build_payload(*, followup: bool, skills_enabled: bool) -> dict:
    return {
        "model": "gpt-5.2-codex",
        "hermes_provider": "openai-codex",
        "stream": False,
        "stream_options": {"include_usage": True},
        "max_tokens": 64,
        "conversation_id": "capture-demo-conversation",
        "messages": _build_messages(followup=followup, skills_enabled=skills_enabled),
        "_capture_meta": {
            "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "capture_scope": "animus_to_hermes_request_payload",
            "skills_enabled": skills_enabled,
            "followup_turn": followup,
            "note": (
                "This capture reflects the ANIMUS request payload sent to Hermes. "
                "It does not include Hermes internal prompt compiler expansions."
            ),
        },
    }


def _api_key_from_env() -> str:
    for key in ("HERMES_API_SERVER_KEY", "API_SERVER_KEY", "HERMES_API_KEY"):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    return ""


def _gateway_capture_one(
    *,
    endpoint_url: str,
    api_key: str,
    payload: dict,
    scenario_name: str,
    dump_dirs: list[Path],
    out_file: Path,
) -> None:
    before_paths = {
        str(p)
        for d in dump_dirs
        for p in d.glob("request_dump_*.json")
    }

    url = endpoint_url.rstrip("/")
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = request.Request(url, data=body, headers=headers, method="POST")

    status_code = 0
    response_text = ""
    try:
        with request.urlopen(req, timeout=30) as resp:
            status_code = int(resp.status)
            response_text = f"HTTP {status_code}"
    except error.HTTPError as e:
        status_code = int(e.code or 0)
        response_text = e.read(2048).decode("utf-8", errors="replace")
    except Exception as e:
        response_text = f"{type(e).__name__}: {e}"

    deadline = time.time() + 12.0
    dump_path: Path | None = None
    while time.time() < deadline:
        new_paths = [
            p
            for d in dump_dirs
            for p in d.glob("request_dump_*.json")
            if str(p) not in before_paths
        ]
        if new_paths:
            dump_path = sorted(new_paths, key=lambda p: p.stat().st_mtime, reverse=True)[0]
            break
        time.sleep(0.3)

    if dump_path is None:
        raise RuntimeError(
            "No Hermes internal request dump was created. "
            f"Ensure gateway is running with HERMES_DUMP_REQUESTS=1. "
            f"Last HTTP status={status_code}, response preview={response_text!r}"
        )

    shutil.copy2(dump_path, out_file)

    sidecar = out_file.with_suffix(".meta.json")
    sidecar_payload = {
        "captured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "capture_scope": "hermes_internal_compiled_request",
        "scenario": scenario_name,
        "gateway_status_code": status_code,
        "gateway_response_preview": response_text,
        "source_dump_file": str(dump_path),
    }
    sidecar.write_text(json.dumps(sidecar_payload, indent=2) + "\n", encoding="utf-8")


def _capture_hermes_internal(
    *,
    repo_root: Path,
    out_dir: Path,
    captures: list[tuple[str, dict]],
    endpoint_url: str,
    api_key: str,
) -> None:
    hermes_home = Path(os.environ.get("HERMES_HOME", str(repo_root / ".hermes"))).expanduser()
    sessions_dir = hermes_home / "sessions"
    logs_dir = hermes_home / "logs"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    dump_dirs = [sessions_dir, logs_dir]

    for name, payload in captures:
        scenario = name.removesuffix(".json")
        internal_name = f"hermes_internal_{scenario}.json"
        _gateway_capture_one(
            endpoint_url=endpoint_url,
            api_key=api_key,
            payload=payload,
            scenario_name=scenario,
            dump_dirs=dump_dirs,
            out_file=out_dir / internal_name,
        )
        print(str(out_dir / internal_name))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--skip-hermes-internal",
        action="store_true",
        help="Only write ANIMUS payload captures (skip Hermes compiled captures).",
    )
    ap.add_argument(
        "--endpoint-url",
        default="http://127.0.0.1:8642/v1/chat/completions",
        help=(
            "POST endpoint that routes to Hermes chat completions. "
            "Use direct gateway URL or an ANIMUS proxy endpoint."
        ),
    )
    ap.add_argument(
        "--api-key",
        default="",
        help="Hermes API server key (defaults to env: HERMES_API_SERVER_KEY/API_SERVER_KEY/HERMES_API_KEY).",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "prompt_captures"
    out_dir.mkdir(parents=True, exist_ok=True)

    captures: list[tuple[str, dict]] = [
        ("skills_enabled_first_session_prompt.json", _build_payload(followup=False, skills_enabled=True)),
        ("skills_enabled_followup_message_prompt.json", _build_payload(followup=True, skills_enabled=True)),
        ("skills_disabled_first_session_prompt.json", _build_payload(followup=False, skills_enabled=False)),
        ("skills_disabled_followup_message_prompt.json", _build_payload(followup=True, skills_enabled=False)),
    ]
    captures = [
        (
            name,
            {
                **payload,
                "conversation_id": f"capture-{name.removesuffix('.json')}",
            },
        )
        for name, payload in captures
    ]

    for name, payload in captures:
        p = out_dir / name
        p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(str(p))

    if args.skip_hermes_internal:
        return 0

    api_key = (args.api_key or "").strip() or _api_key_from_env()
    _capture_hermes_internal(
        repo_root=repo_root,
        out_dir=out_dir,
        captures=captures,
        endpoint_url=args.endpoint_url,
        api_key=api_key,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
