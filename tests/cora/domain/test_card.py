import pytest

from cora.domain.card import (
    ActionOffered,
    Card,
    FieldAsked,
    fields_of,
)
from cora.domain.decision import Decision, Option, Pending

SCHEMA = {
    "type": "object",
    "properties": {
        "origin": {"type": "string"},
        "nights": {"type": "integer"},
    },
    "required": ["origin"],
}
SEARCH = ActionOffered(label="Search", answer="Search")


def test_a_card_carries_a_prompt_its_fields_and_its_actions() -> None:
    card = Card(
        prompt="Give me the trip.",
        fields=fields_of(SCHEMA, {"origin": "BER"}),
        actions=(SEARCH,),
    )

    assert card.prompt == "Give me the trip."
    assert [field.name for field in card.fields] == ["origin", "nights"]
    assert [action.label for action in card.actions] == ["Search"]


def test_a_card_nobody_can_leave_is_refused() -> None:
    """The page has nothing else to offer while a card is open."""
    with pytest.raises(ValueError):
        Card(prompt="Give me the trip.")


def test_a_card_whose_every_action_waits_for_it_is_refused() -> None:
    """The page disables the composer while a card is open, so a card the reader cannot
    get off is a conversation they cannot leave — and an action that waits for the
    required fields is no way out of a card they cannot fill."""
    with pytest.raises(ValueError):
        Card(
            prompt="Give me the trip.",
            fields=(FieldAsked(name="origin", required=True),),
            actions=(ActionOffered(label="Search", answer="Search", needs_valid=True),),
        )


def test_a_field_carries_its_schema_what_is_known_and_whether_it_is_the_readers() -> (
    None
):
    """The schema a tool declares is the one the card asks on, so the two cannot
    drift."""
    origin, nights = fields_of(SCHEMA, {"origin": "BER"})

    assert (origin.value, origin.required, origin.editable) == ("BER", True, True)
    assert (nights.value, nights.required) == (None, False)
    assert nights.schema == {"type": "integer"}


def test_a_decision_is_a_card_of_no_fields_and_one_action_per_option() -> None:
    card = Decision(
        question="Which weight?",
        options=(Option(label="77 kg", note="intake form"), Option(label="75 kg")),
        decline="Neither of them",
    ).card

    assert card.fields == ()
    assert [(action.label, action.answer) for action in card.actions] == [
        ("77 kg", "77 kg"),
        ("75 kg", "75 kg"),
        ("Neither of them", None),
    ]
    assert card.actions[0].note == "intake form"


def test_a_parked_turn_carries_the_card_whatever_stopped_it() -> None:
    parked = Pending(asked="What is my BMR?", card=Decision(question="Which?").card)

    assert parked.card.prompt == "Which?"


def test_a_schema_asked_over_yields_a_field_per_property_however_many_are_known() -> (
    None
):
    """What a card built from a schema asks for is every property, filled or not — so a
    call missing one of two arguments still puts two boxes, one of them already
    written in. The plugin how-to's example turns on this."""
    schema = {
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "depart": {"type": "string", "format": "date"},
        },
        "required": ["origin", "depart"],
    }

    fields = fields_of(schema, {"origin": "BER"})

    assert [(field.name, field.value) for field in fields] == [
        ("origin", "BER"),
        ("depart", None),
    ]
    assert all(field.editable for field in fields)
