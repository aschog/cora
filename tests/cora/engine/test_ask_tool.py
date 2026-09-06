import pytest

from cora.domain.decision import Decision, Option
from cora.engine.ask_tool import (
    ASK_TOOL_NAME,
    ASKED_ALREADY,
    MOST_FIELDS,
    SEND,
    ask_for_tool,
    ask_tool,
    card_from,
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


WANTED = "Give me the trip and I'll price it."


def _asking(*fields: dict) -> dict:
    return {"prompt": WANTED, "fields": list(fields)}


def test_an_ask_for_three_values_is_a_card_of_three_fields() -> None:
    card = card_from(
        _asking(
            {"name": "origin", "description": "Where you are flying from"},
            {"name": "depart", "description": "The day you leave"},
            {"name": "nights", "description": "How many nights away"},
        )
    )

    assert card.prompt == WANTED
    assert [field.name for field in card.fields] == ["origin", "depart", "nights"]
    assert all(field.editable for field in card.fields), "a form is written in"


def test_a_field_carries_the_schema_of_the_value_it_asks_for() -> None:
    card = card_from(
        _asking(
            {"name": "depart", "description": "The day you leave", "format": "date"},
            {"name": "nights", "description": "How many", "type": "integer"},
            {"name": "budget", "description": "Spend", "choices": ["Lean", "No cap"]},
        )
    )

    day, nights, budget = card.fields
    assert day.schema == {
        "type": "string",
        "description": "The day you leave",
        "format": "date",
    }
    assert nights.schema["type"] == "integer"
    assert budget.schema["enum"] == ["Lean", "No cap"]


def test_a_field_the_ask_calls_required_is_required_on_the_card() -> None:
    card = card_from(
        _asking(
            {"name": "origin", "description": "From", "required": True},
            {"name": "budget", "description": "Spend"},
        )
    )

    assert [field.required for field in card.fields] == [True, False]


def test_the_card_offers_a_way_out_beside_the_one_that_submits() -> None:
    """A card the reader cannot leave is a conversation they cannot leave, and the one
    that submits waits for the fields the ask called required."""
    card = card_from(_asking({"name": "origin", "description": "From"}))

    send, out = card.actions
    assert (send.answer, send.needs_valid) == (SEND, True)
    assert out.answer is None, "the way out settles the ask and writes nothing"


def test_an_ask_for_no_values_at_all_is_refused() -> None:
    """Refused where it was made rather than drawn: an empty card is one the reader
    cannot answer, and it would spend the turn's one question."""
    with pytest.raises(ToolRefusal):
        card_from({"prompt": WANTED, "fields": []})


def test_a_field_with_no_name_is_refused() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_from(_asking({"description": "Where you are flying from"}))

    assert "name" in str(refused.value)


def test_a_field_of_a_type_cora_cannot_read_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_from(_asking({"name": "origin", "description": "From", "type": "map"}))


def test_two_fields_of_the_same_name_are_refused() -> None:
    """Silently keeping one of them would ask for less than the model asked for, and
    the answer would rest on a value nobody was shown a box for."""
    with pytest.raises(ToolRefusal) as refused:
        card_from(
            _asking(
                {"name": "origin", "description": "Where from"},
                {"name": "origin", "description": "Where from, again"},
            )
        )

    assert "origin" in str(refused.value)


def test_neither_ask_reads_as_the_other() -> None:
    """The model picks by shape, so each description names the case it is for: one
    settles a fact between values already found, the other gathers what nobody has."""
    settling = ask_tool().description
    gathering = ask_for_tool().description

    assert "two or more different values" in settling
    assert "do not have and cannot look up" in gathering
    assert "option" not in gathering, "options are the other ask's, and a form has none"


def test_an_ask_with_no_prompt_to_read_is_refused() -> None:
    """A card whose prompt is blank asks the reader for values and never says what for
    — and the trace, having no question to show, would fall back to the fields."""
    with pytest.raises(ToolRefusal):
        card_from({"prompt": "", "fields": [{"name": "origin", "description": "From"}]})


def test_a_form_longer_than_anyone_fills_is_refused() -> None:
    """A wall of controls is a card the reader abandons, and abandoning it tells the
    model nothing. Refused, the model asks for what the answer turns on instead."""
    with pytest.raises(ToolRefusal):
        card_from(
            _asking(
                *(
                    {"name": f"field_{at}", "description": "Something"}
                    for at in range(MOST_FIELDS + 1)
                )
            )
        )
