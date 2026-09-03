"""What cora is about to change outside itself, and the yes or no bound to it."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Proposed:
    """One call that would change something outside cora, put to the user first.

    `does` is what the tool says it does, in the tool's own words, and `arguments` are
    as the model wrote them: what is approved is this call and not the idea of it.
    `call_id` is the provider's, and it is what binds an answer to this proposal —
    a round may propose two effects, and neither may be settled by the other's yes.
    """

    call_id: str
    tool: str
    does: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Approval:
    """The answer to one proposal: this call, and whether it may run.

    Its own type rather than an option on a `Decision`, because a label is bound to
    nothing — the second effect of a round would have no way of saying which of the two
    it settled. `approved` defaults to false: a shape arriving half-built refuses.
    """

    call_id: str
    approved: bool = False


def approves(proposed: Proposed, answer: object) -> bool:
    """Whether what came back is an approval of this very call.

    The answer reached the run from outside it, so it is read rather than trusted:
    anything that is not this call's own yes leaves the call unapproved, which is what
    makes a decline the default and not an outcome someone has to remember to send.
    """
    return (
        isinstance(answer, Approval)
        and answer.call_id == proposed.call_id
        and answer.approved
    )
