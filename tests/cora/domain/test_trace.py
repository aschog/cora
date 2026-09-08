from cora.domain.trace import (
    ModelDecision,
    ToolUse,
    WorkShown,
)


def test_a_decision_names_the_tools_it_asked_for() -> None:
    decision = ModelDecision(tools=("search_documents", "add"))

    assert decision.summary == "Decided to call search_documents and add"


def test_a_tool_use_shows_its_name_arguments_and_outcome() -> None:
    use = ToolUse(
        name="search_documents",
        arguments={"query": "protein"},
        outcome="1 passage from note.md",
    )

    assert use.summary == 'search_documents(query="protein") → 1 passage from note.md'


def test_a_failed_tool_use_is_marked_and_carries_the_error() -> None:
    use = ToolUse(
        name="add", arguments={"a": 1}, outcome="invalid arguments", failed=True
    )

    assert use.failed
    assert use.summary == "add(a=1) → invalid arguments"


def test_a_step_read_back_from_data_holds_the_tuples_it_declares() -> None:
    """JSON has one sequence, and both doors a step travels through — the checkpoint and
    the conversation store — hand its fields back as keyword arguments. A step that came
    back holding lists would stop being equal to the step that was recorded, and the
    trace a resumed turn compares against would never match."""
    restored = ToolUse(
        name="research",
        arguments={"q": 1},
        outcome="ok",
        steps=[ModelDecision(detail="looking", tools=["add"])],  # ty: ignore[invalid-argument-type]
    )

    assert restored == ToolUse(
        name="research",
        arguments={"q": 1},
        outcome="ok",
        steps=(ModelDecision(detail="looking", tools=("add",)),),
    )
    assert isinstance(restored.steps, tuple)
    [inside] = restored.steps
    assert isinstance(inside, ModelDecision)
    assert isinstance(inside.tools, tuple)


def test_a_plugin_s_own_line_is_summarised_as_the_plugin_and_what_it_did() -> None:
    shown = WorkShown(plugin="acme.plugins.birds", did="counted 3 wrens")

    assert shown.summary == "acme.plugins.birds counted 3 wrens"


def test_a_plugin_s_own_line_marked_as_gone_wrong_reads_as_failed() -> None:
    assert WorkShown(plugin="acme", did="lost count", failed=True).failed
