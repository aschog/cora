"""What cora is about to change outside itself, and the yes or no bound to it."""

from dataclasses import dataclass, field
from typing import Any

from cora.domain.card import ActionOffered, Answer, Card, FieldAsked

APPROVE = "Approve"
DECLINE = "Decline"
APPROVED = "You approved it."
DECLINED = "You declined it. Nothing outside cora was changed."
TOOL = "the tool"


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

    @property
    def card(self) -> Card:
        """This, as the reader is shown it: the call laid out, and nothing writable.

        The tool and every argument are fields the reader reads, because what is
        approved is this call and not the idea of it. The yes carries the call's own id,
        so a round that proposed two effects cannot have one settled by the other's.
        """
        return Card(
            prompt=self.does,
            fields=(
                FieldAsked(name=TOOL, value=self.tool, editable=False),
                *(
                    FieldAsked(name=name, value=value, editable=False)
                    for name, value in self.arguments.items()
                ),
            ),
            actions=(
                ActionOffered(label=APPROVE, answer=self.call_id, settled=APPROVED),
                ActionOffered(label=DECLINE, answer=None, settled=DECLINED),
            ),
        )


def approves(proposed: Proposed, answer: object) -> bool:
    """Whether what came back is an approval of this very call.

    The answer reached the run from outside it, so it is read rather than trusted:
    anything that is not this call's own id leaves the call unapproved, which is what
    makes a decline the default and not an outcome someone has to remember to send. A
    label is bound to nothing, so the id is what an approve action carries.
    """
    return isinstance(answer, Answer) and answer.action == proposed.call_id
