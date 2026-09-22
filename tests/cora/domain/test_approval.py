from cora.domain.approval import APPROVE, DECLINE, TOOL, Proposed, approves
from cora.domain.card import Answer

PROPOSED = Proposed(
    call_id="c1", tool="save_itinerary", does="Save an itinerary", arguments={"a": 1}
)


def test_only_an_answer_naming_this_very_call_approves_it() -> None:
    assert approves(PROPOSED, Answer(action="c1"))
    assert not approves(PROPOSED, Answer(action=None))
    assert not approves(PROPOSED, Answer(action="c2"))
    assert not approves(PROPOSED, "yes")
    assert not approves(PROPOSED, None)


def test_a_proposal_is_a_card_of_the_call_and_nothing_writable() -> None:
    card = PROPOSED.card

    assert card.prompt == "Save an itinerary"
    assert [(field.name, field.value) for field in card.fields] == [
        (TOOL, "save_itinerary"),
        ("a", 1),
    ]
    assert not any(field.editable for field in card.fields)


def test_approving_carries_the_call_id_and_declining_carries_nothing() -> None:
    approve, decline = PROPOSED.card.actions

    assert (approve.label, approve.answer) == (APPROVE, "c1")
    assert (decline.label, decline.answer) == (DECLINE, None)
