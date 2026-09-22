from cora.domain.trace import (
    CardFilled,
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


def test_a_card_the_reader_filled_in_says_so_and_one_they_left_says_that() -> None:
    assert CardFilled(tool="price_it", fields=("origin",)).summary == (
        "You filled in price_it"
    )
    assert CardFilled(tool="price_it").summary == "You gave price_it nothing"


def test_a_card_that_asked_for_nothing_says_the_reader_let_it_run() -> None:
    confirmed = CardFilled(tool="price_it", asked=False)

    assert confirmed.summary == "You confirmed price_it"
