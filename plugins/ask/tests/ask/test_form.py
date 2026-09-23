import pytest

from cora.plugins.ask.form import (
    ASK_FOR_SCHEMA,
    MOST_FIELDS,
    NOTHING_WRITTEN,
    card_of_form,
    fill,
)
from cora.ports.plugin import ToolRefusal

WANTED = "Give me the trip and I'll price it."


def _asking(*fields: dict) -> dict:
    return {"prompt": WANTED, "fields": list(fields)}


def test_an_ask_for_three_values_is_a_card_of_three_fields() -> None:
    card = card_of_form(
        _asking(
            {"name": "origin", "description": "Where you are flying from"},
            {"name": "depart", "description": "The day you leave"},
            {"name": "nights", "description": "How many nights away"},
        )
    )

    assert card.prompt == WANTED
    assert [field.name for field in card.fields] == ["origin", "depart", "nights"]
    assert all(field.editable for field in card.fields), "a form is written in"
    assert card.lands == "", "a form settles on what was written, not on a button"


def test_a_field_the_ask_calls_required_is_required_on_the_card() -> None:
    card = card_of_form(
        _asking(
            {"name": "origin", "description": "From", "required": True},
            {"name": "budget", "description": "Spend"},
        )
    )

    assert [field.required for field in card.fields] == [True, False]


def test_a_field_of_a_type_cora_cannot_read_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_of_form(_asking({"name": "origin", "description": "From", "type": "map"}))


def test_two_fields_of_the_same_name_are_refused() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_of_form(
            _asking(
                {"name": "origin", "description": "Where from"},
                {"name": "origin", "description": "Where from, again"},
            )
        )

    assert "origin" in str(refused.value)


def test_a_form_of_one_value_is_refused_by_the_tool_the_model_reads() -> None:
    with pytest.raises(ToolRefusal) as refused:
        card_of_form(_asking({"name": "height", "description": "Your height"}))

    assert "height" in str(refused.value), "the message names the value to ask for"


def test_a_form_of_one_field_that_is_not_even_a_field_is_still_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_of_form({"prompt": WANTED, "fields": ["height"]})

    with pytest.raises(ToolRefusal):
        card_of_form({"prompt": WANTED, "fields": [{"description": "No name"}]})


def test_the_form_tool_declares_that_it_takes_two_values_or_more() -> None:
    assert ASK_FOR_SCHEMA["properties"]["fields"]["minItems"] == 2


def test_a_form_longer_than_anyone_fills_is_refused() -> None:
    with pytest.raises(ToolRefusal):
        card_of_form(
            _asking(
                *(
                    {"name": f"field_{at}", "description": "Something"}
                    for at in range(MOST_FIELDS + 1)
                )
            )
        )


def test_what_the_reader_wrote_is_what_the_model_is_told() -> None:
    said = fill(prompt=WANTED, fields=[], origin="BER", depart="2026-10-01")

    assert "'BER'" in said and "'2026-10-01'" in said


def test_a_form_nobody_wrote_in_says_so() -> None:
    assert fill(prompt=WANTED, fields=[]) == NOTHING_WRITTEN
