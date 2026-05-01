"""Regression: ANIMUS in-chat digest must not be frozen into sessions.system_prompt."""

from animus_chat_digest_persist import strip_animus_transient_chat_digest_for_session_persist as strip


def test_strip_digest_only_ephemeral():
    e = "[In-chat session digest (local).]\n\nline1\n\nline2"
    assert strip(e) == ""


def test_strip_digest_before_project_block():
    digest = "[In-chat session digest (1/1/26).]\n\nDense recall body."
    proj = '\n\nProject "MyApp" · workspace: /tmp/foo — use it as cwd'
    out = strip(digest + proj)
    assert "Dense recall body" not in out
    assert 'Project "MyApp"' in out


def test_strip_legacy_prior_summary_marker():
    e = '[Prior conversation summarized.]\n\nold digest\n\nANIMUS capability note: x'
    out = strip(e)
    assert "old digest" not in out
    assert "ANIMUS capability note" in out


def test_strip_noop_without_marker():
    assert strip("plain project system only") == "plain project system only"
