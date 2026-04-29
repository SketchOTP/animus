"""
Append cron job output into Hermes Chat server-side transcripts.

Hermes Chat stores ``conversations.json`` under the resolved chat data directory
(same rules as ``hermes-chat/server.py`` and ``agent.project_workspace.hermes_chat_data_dir``:
``CHAT_DATA_DIR`` / ``HERMES_CHAT_DATA_DIR``, then ``~/.hermes/.env``, else
``~/.hermes/chat``).  Prefer exporting ``CHAT_DATA_DIR`` on the gateway/cron unit
to match the Chat server when it is not the default.

Delivery target syntax (``deliver`` field, resolved in ``cron.scheduler``):

* A **bare RFC-4122 UUID** (no ``:``) → Hermes Chat **project** ``Cron updates`` thread.
* ``hermes-chat:<uuid>`` / ``hermes-chat:project:<uuid>`` — same as bare UUID.
* ``hermes-chat:conv:<uuid>`` — append to that conversation id.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.project_workspace import hermes_chat_data_dir

logger = logging.getLogger(__name__)

_CRON_CONV_TITLE = "Cron updates"

# Hermes Chat project ids are UUIDs; normalize case so delivery matches ``projects.json``.
_PROJECT_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z",
    re.I,
)


def _normalize_project_target_id(kind: str, target_id: str) -> str:
    t = (target_id or "").strip()
    if kind == "project" and t and _PROJECT_UUID_RE.match(t):
        return t.lower()
    return t


def _project_ids_equal(stored: Any, wanted: str) -> bool:
    if stored is None or wanted is None:
        return False
    a = str(stored).strip()
    b = str(wanted).strip()
    if _PROJECT_UUID_RE.match(a) and _PROJECT_UUID_RE.match(b):
        return a.lower() == b.lower()
    return a == b


def _conversations_path() -> Path:
    p = hermes_chat_data_dir() / "conversations.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _try_flock_ex(lock_fd: int) -> bool:
    try:
        import fcntl

        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        return True
    except ImportError:
        return False


def _flock_un(lock_fd: int) -> None:
    try:
        import fcntl

        fcntl.flock(lock_fd, fcntl.LOCK_UN)
    except ImportError:
        pass


def append_cron_to_hermes_chat(
    *,
    kind: str,
    target_id: str,
    text: str,
    job_id: str = "",
    job_name: str = "",
) -> None:
    """Append one assistant message to the Hermes Chat JSON store.

    Args:
        kind: ``project`` or ``conversation``.
        target_id: Project id or conversation id.
        text: Body (already wrapped by cron scheduler when applicable).
        job_id / job_name: For logging only.
    """
    tid = _normalize_project_target_id(kind, str(target_id or ""))
    if not tid:
        raise ValueError("Hermes Chat delivery target id is empty")
    body = (text or "").strip()
    if not body:
        body = "(empty cron output)"

    path = _conversations_path()
    logger.info("Hermes Chat cron delivery writing conversations.json under %s", path.parent)
    lock_path = path.with_suffix(".json.flock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_f = open(lock_path, "a+", encoding="utf-8")
    try:
        if not _try_flock_ex(lock_f.fileno()):
            logger.warning(
                "Hermes Chat cron delivery: fcntl unavailable — proceeding without file lock"
            )

        convs: list[dict[str, Any]]
        if path.exists():
            try:
                raw = path.read_text(encoding="utf-8")
                convs = json.loads(raw) if raw.strip() else []
            except json.JSONDecodeError as e:
                raise RuntimeError(f"corrupt conversations.json: {e}") from e
        else:
            convs = []

        if not isinstance(convs, list):
            raise RuntimeError("conversations.json must contain a JSON array")

        msg: dict[str, Any] = {"role": "assistant", "content": body, "source": "cron"}
        if job_id:
            msg["cron_job_id"] = job_id
        if job_name:
            msg["cron_job_name"] = job_name

        if kind == "conversation":
            conv = next((c for c in convs if c.get("id") == tid), None)
            if not conv:
                raise ValueError(f"No Hermes Chat conversation with id {tid!r}")
            messages = conv.setdefault("messages", [])
            if not isinstance(messages, list):
                raise RuntimeError("conversation.messages must be a list")
            messages.append(msg)
        elif kind == "project":
            conv = next(
                (
                    c
                    for c in convs
                    if _project_ids_equal(c.get("project_id"), tid)
                    and c.get("title") == _CRON_CONV_TITLE
                ),
                None,
            )
            if not conv:
                conv = {
                    "id": str(uuid.uuid4()),
                    "project_id": tid,
                    "session_id": str(uuid.uuid4()),
                    "title": _CRON_CONV_TITLE,
                    "notification_channel": "cron",
                    "created_at": _iso_now(),
                    "messages": [],
                }
                convs.insert(0, conv)
            elif not conv.get("notification_channel"):
                conv["notification_channel"] = "cron"
            messages = conv.setdefault("messages", [])
            if not isinstance(messages, list):
                raise RuntimeError("conversation.messages must be a list")
            messages.append(msg)
        else:
            raise ValueError(f"unknown Hermes Chat delivery kind {kind!r}")

        tmp = path.with_suffix(".tmp")
        data = json.dumps(convs, ensure_ascii=False, indent=2)
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(path)

        logger.info(
            "Hermes Chat cron delivery: job=%s name=%r kind=%s target=%s messages=%d",
            job_id,
            job_name,
            kind,
            tid,
            len(messages),
        )
        if kind == "project":
            try:
                from agent.project_workspace import append_history_for_cron_delivery

                append_history_for_cron_delivery(
                    tid,
                    job_name=job_name or "",
                    job_id=job_id or "",
                    text_preview=body[:400],
                )
            except Exception as exc:
                logger.warning(
                    "Hermes Chat cron delivery: project_history append failed: %s",
                    exc,
                )
    finally:
        _flock_un(lock_f.fileno())
        lock_f.close()
