from cora.domain.trace import ModelDecision, StepEntered, ToolUse


def test_a_decision_names_the_tools_it_asked_for() -> None:
    decision = ModelDecision(tools=("search_documents", "add"))

    assert decision.summary == "Decided to call search_documents and add"


def test_a_decision_that_asked_for_no_tool_says_so() -> None:
    assert ModelDecision().summary == "Decided no tool was needed"


def test_a_tool_use_shows_its_name_arguments_and_outcome() -> None:
    use = ToolUse(
        name="search_documents",
        arguments={"query": "protein"},
        outcome="1 passage from note.md",
    )

    assert use.summary == 'search_documents(query="protein") → 1 passage from note.md'


def test_arguments_keep_the_order_they_were_called_with() -> None:
    use = ToolUse(name="add", arguments={"a": 20, "b": 22}, outcome="42")

    assert use.summary == "add(a=20, b=22) → 42"


def test_a_tool_called_with_no_arguments_shows_the_bare_name() -> None:
    use = ToolUse(name="today", arguments={}, outcome="2026-08-11")

    assert use.summary == "today() → 2026-08-11"


def test_a_failed_tool_use_is_marked_and_carries_the_error() -> None:
    use = ToolUse(
        name="add", arguments={"a": 1}, outcome="invalid arguments", failed=True
    )

    assert use.failed
    assert use.summary == "add(a=1) → invalid arguments"


def test_a_step_the_turn_entered_is_named_by_the_step() -> None:
    assert StepEntered("screen").summary == "Started to screen"
