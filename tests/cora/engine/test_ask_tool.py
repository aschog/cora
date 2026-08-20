import pytest

from cora.domain.decision import Decision, Option
from cora.engine.ask_tool import (
    ASK_TOOL_NAME,
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
    settled = decision_from({"question": ASKED, "options": [{"label": "75 kg"}]})

    assert settled.options == (Option(label="75 kg"),)
    assert settled.decline == "", "nothing offered is nothing drawn"


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


def test_running_the_tool_refuses_rather_than_answering_without_asking() -> None:
    """The router settles an `ask_user` call before the round's tools run, so the
    dispatcher never reaches this. If it ever did, a returned value would be an answer
    nobody was asked for."""
    with pytest.raises(ToolRefusal):
        ask_tool().run(question=ASKED, options=[{"label": "75 kg"}])
