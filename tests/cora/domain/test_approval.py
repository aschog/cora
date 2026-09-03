import pytest

from cora.domain.approval import Approval, Proposed, approves
from cora.domain.decision import Decision, Pending

PROPOSED = Proposed(
    call_id="c1", tool="save_itinerary", does="Save an itinerary", arguments={"a": 1}
)


def test_only_an_approval_of_this_very_call_approves_it() -> None:
    """Whatever answers the gate arrived from outside the run, so it is checked rather
    than trusted: a yes to another call, a label nobody asked for, or nothing at all
    leaves the call unapproved."""
    assert approves(PROPOSED, Approval(call_id="c1", approved=True))
    assert not approves(PROPOSED, Approval(call_id="c1", approved=False))
    assert not approves(PROPOSED, Approval(call_id="c2", approved=True))
    assert not approves(PROPOSED, "yes")
    assert not approves(PROPOSED, None)


def test_a_parked_turn_stopped_on_a_proposal_or_on_a_decision_and_never_on_both() -> (
    None
):
    """One thread stops one way at a time. Two shapes would make the page ask which it
    was; none is a pause carrying nothing to settle."""
    assert Pending(asked="q", proposal=PROPOSED).decision is None
    assert Pending(asked="q", decision=Decision(question="which?")).proposal is None
    with pytest.raises(ValueError):
        Pending(asked="q", decision=Decision(question="which?"), proposal=PROPOSED)
    with pytest.raises(ValueError):
        Pending(asked="q")
