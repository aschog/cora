import pytest

from cora.domain.decision import Decision, Option
from cora.engine.ask_tool import (
    ASK_TOOL_NAME,
    ASKED_ALREADY,
    ask_tool,
    decision_from,
)
from cora.ports.plugin import ToolRefusal

ASKED = "Which bodyweight should I treat as current?"


def test_a_call_becomes_the_decision_it_describes() -> None:
    settled = decision_from(
        {
            "question": ASKED,
            "options": [
                {"label": "77 kg", "note": "intake form, 17 Aug"},
                {"label": "75 kg", "note": "coach notes, February"},
            ],
            "decline": "Don't use any of them",
        }
    )

    assert settled == Decision(
        question=ASKED,
        options=(
            Option(label="77 kg", note="intake form, 17 Aug"),
            Option(label="75 kg", note="coach notes, February"),
        ),
        decline="Don't use any of them",
    )


def test_an_option_is_a_label_alone_when_the_model_offers_no_note() -> None:
    settled = decision_from(
        {"question": ASKED, "options": [{"label": "75 kg"}, {"label": "77 kg"}]}
    )

    assert settled.options == (Option(label="75 kg"), Option(label="77 kg"))
    assert settled.decline == "", "nothing offered is nothing drawn"


def test_a_fork_with_one_way_out_of_it_is_refused() -> None:
    """A card with a single button is a question with no question in it, and the page
    disables the composer while one is open — so the reader would be left with one thing
    to click and nothing to decide."""
    with pytest.raises(ToolRefusal):
        decision_from({"question": ASKED, "options": [{"label": "75 kg"}]})


def test_a_call_with_no_options_is_refused_in_words_the_model_can_read() -> None:
    """A refusal, not an exception: the round is told what was wrong with the ask and
    carries on, the way it would for a malformed call to any other tool."""
    with pytest.raises(ToolRefusal) as refused:
        decision_from({"question": ASKED})

    assert "options" in str(refused.value)


def test_a_call_with_an_option_that_is_not_labelled_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        decision_from({"question": ASKED, "options": [{"note": "no label"}]})


def test_the_tool_offers_the_schema_a_decision_is_read_from() -> None:
    offered = ask_tool()

    assert offered.name == ASK_TOOL_NAME
    assert offered.parameter_schema["required"] == ["question", "options"]


def test_running_the_tool_says_the_turn_has_already_asked() -> None:
    """The dispatcher reaches the tool only for an ask the run will not stop on — a
    second one in the same round, or one after the reader has been stopped. The round
    can act on that reason; it can act on nothing at all."""
    with pytest.raises(ToolRefusal) as refused:
        ask_tool().run(question=ASKED, options=[{"label": "75 kg"}])

    assert ASKED_ALREADY in str(refused.value)
