import pytest

from cora.domain.decision import Decision, Option
from cora.engine.ask_tool import (
    ASK_TOOL_NAME,
    MOST_FIELDS,
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


def test_a_fork_with_one_way_out_of_it_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        decision_from({"question": ASKED, "options": [{"label": "75 kg"}]})


def test_a_call_with_no_options_is_refused_in_words_the_model_can_read() -> None:
    with pytest.raises(ToolRefusal) as refused:
        decision_from({"question": ASKED})

    assert "options" in str(refused.value)


def test_the_tool_offers_the_schema_a_decision_is_read_from() -> None:
    offered = ask_tool()

    assert offered.name == ASK_TOOL_NAME
    assert offered.parameter_schema["required"] == ["question", "options"]


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


def test_a_field_the_ask_calls_required_is_required_on_the_card() -> None:
    card = card_from(
        _asking(
            {"name": "origin", "description": "From", "required": True},
            {"name": "budget", "description": "Spend"},
        )
    )

    assert [field.required for field in card.fields] == [True, False]


def test_a_field_of_a_type_cora_cannot_read_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_from(_asking({"name": "origin", "description": "From", "type": "map"}))


def test_two_fields_of_the_same_name_are_refused() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_from(
            _asking(
                {"name": "origin", "description": "Where from"},
                {"name": "origin", "description": "Where from, again"},
            )
        )

    assert "origin" in str(refused.value)


def test_a_form_of_one_value_is_refused_by_the_tool_the_model_reads() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_from(_asking({"name": "height", "description": "Your height"}))

    assert "height" in str(refused.value), "the message names the value to ask for"


def test_a_form_of_one_field_that_is_not_even_a_field_is_still_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_from({"prompt": WANTED, "fields": ["height"]})

    with pytest.raises(ToolRefusal):
        card_from({"prompt": WANTED, "fields": [{"description": "No name"}]})


def test_the_form_tool_declares_that_it_takes_two_values_or_more() -> None:
    offered = ask_for_tool()

    assert offered.parameter_schema["properties"]["fields"]["minItems"] == 2


def test_a_form_longer_than_anyone_fills_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_from(
            _asking(
                *(
                    {"name": f"field_{at}", "description": "Something"}
                    for at in range(MOST_FIELDS + 1)
                )
            )
        )
