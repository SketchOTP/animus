from agent.task_complexity import estimate_task_complexity


def test_estimate_low_from_markers():
    assert (
        estimate_task_complexity(
            goal="quick typo fix in readme",
            context="",
            toolsets=None,
            task_count=1,
        )
        == "low"
    )


def test_estimate_high_from_markers():
    assert (
        estimate_task_complexity(
            goal="Design a full security migration for multi-file architecture",
            context="",
            toolsets=None,
            task_count=1,
        )
        == "high"
    )


def test_history_len_increases_score():
    low_text = "rename variable x to y"
    assert estimate_task_complexity(goal=low_text, history_message_count=0) == "low"
    assert estimate_task_complexity(goal=low_text, history_message_count=60) != "low"
