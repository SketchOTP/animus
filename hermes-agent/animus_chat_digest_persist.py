"""Strip ANIMUS-only transient system text before persisting gateway chat ephemerals to SQLite."""

_ANIMUS_CHAT_DIGEST_MARKERS = (
    "[In-chat session digest",
    "[Prior conversation summarized",  # legacy ANIMUS client header
)


def strip_animus_transient_chat_digest_for_session_persist(ephemeral: str) -> str:
    """Remove ANIMUS in-chat ``context_digest`` blocks from gateway ``ephemeral_system_prompt``.

    ANIMUS prepends a session digest into the OpenAI ``messages`` system layer each turn. That
    blob must **not** be merged into ``sessions.system_prompt`` on first HTTP persist: the next
    turn loads the stored row (already containing the digest) and ``run_conversation`` also
    appends ``ephemeral_system_prompt`` again, duplicating the digest and inflating input tokens.
    """
    s = (ephemeral or "").strip()
    if not s:
        return s
    key_idx = -1
    for m in _ANIMUS_CHAT_DIGEST_MARKERS:
        j = s.find(m)
        if j >= 0 and (key_idx < 0 or j < key_idx):
            key_idx = j
    if key_idx < 0:
        return s
    rest = s[key_idx:]
    ends: list[int] = []
    pm = rest.find('\n\nProject "')
    if pm > 0:
        ends.append(pm)
    sk = rest.find("\n\nANIMUS capability note:")
    if sk > 0:
        ends.append(sk)
    if ends:
        cut = key_idx + min(ends)
        return (s[:key_idx] + s[cut:]).strip()
    return s[:key_idx].strip()
