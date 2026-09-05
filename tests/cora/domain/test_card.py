import pytest

from cora.domain.card import (
    ActionOffered,
    Answer,
    Asks,
    Card,
    fields_of,
    missing_from,
)
from cora.domain.decision import NO_OPTION, Decision, Option, Pending

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


def test_a_card_is_its_own_asks_so_one_port_puts_every_kind() -> None:
    card = Card(prompt="Give me the trip.", actions=(SEARCH,))

    assert isinstance(card, Asks)
    assert card.card is card


def test_a_field_carries_its_schema_what_is_known_and_whether_it_is_the_readers() -> (
    None
):
    """The schema a tool declares is the one the card asks on, so the two cannot
    drift."""
    origin, nights = fields_of(SCHEMA, {"origin": "BER"})

    assert (origin.value, origin.required, origin.editable) == ("BER", True, True)
    assert (nights.value, nights.required) == (None, False)
    assert nights.schema == {"type": "integer"}


def test_fields_of_a_call_put_up_to_be_read_are_not_writable() -> None:
    assert not any(field.editable for field in fields_of(SCHEMA, {}, editable=False))


def test_what_a_call_still_has_to_be_told() -> None:
    """A required property nobody gave a value for. Blank counts as nothing: an empty
    control means unanswered."""
    assert missing_from(SCHEMA, {}) == ("origin",)
    assert missing_from(SCHEMA, {"origin": ""}) == ("origin",)
    assert missing_from(SCHEMA, {"origin": "BER"}) == ()
    assert missing_from({"properties": {}}, {}) == ()


def test_an_answer_of_no_values_settles_on_the_action_alone() -> None:
    assert Answer(action="Search").values == {}


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


def test_a_decision_the_model_wrote_no_way_out_of_still_has_one() -> None:
    """The page disables the composer while a card is open, so a card with nothing to
    click is a conversation the reader cannot leave."""
    card = Decision(question="Which weight?", options=(Option(label="77 kg"),)).card

    assert card.actions[-1] == ActionOffered(
        label=NO_OPTION, answer=None, settled="You chose none of them."
    )


def test_a_parked_turn_carries_the_card_whatever_stopped_it() -> None:
    parked = Pending(asked="What is my BMR?", card=Decision(question="Which?").card)

    assert parked.card.prompt == "Which?"
