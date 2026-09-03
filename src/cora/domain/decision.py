"""What cora stops a turn to ask, and how a parked turn is carried."""

from dataclasses import dataclass

from cora.domain.approval import Proposed

APPROVAL_OF = "{tool} is waiting for your approval"
"""What a turn parked on a proposal is, in one line — the message the pause carries
where a question would have carried its own."""


@dataclass(frozen=True)
class Option:
    """One way the run could go.

    `note` is where the value came from, which is what makes two of these tellable
    apart by whoever has to choose.
    """

    label: str
    note: str = ""


@dataclass(frozen=True)
class Decision:
    """What cora stopped to have settled, in its own words.

    The options are the model's rather than a rule's: ranking two remembered values
    against each other is reading them and where each came from, which no mark on a
    tool can do. `decline` is the way out of the fork: `ask_user` is what refuses a
    question that offers no way on, so nothing here has to.
    """

    question: str
    options: tuple[Option, ...] = ()
    decline: str = ""


@dataclass(frozen=True)
class Pending:
    """A turn parked on something the user has to settle: a decision, or a proposal.

    `asked` is the question the turn opened with, kept beside what stopped it because a
    paused turn is in no store yet and the page has to draw the card under the question
    that raised it.

    Exactly one of `decision` and `proposal` is carried. One thread stops one way at a
    time, and a shape that could claim both would make the page ask which it was.
    """

    asked: str
    decision: Decision | None = None
    proposal: Proposed | None = None

    def __post_init__(self) -> None:
        """Refuse a parked turn with nothing to settle, or with two things.

        Raises:
            ValueError: Both a decision and a proposal were given, or neither was.
        """
        if (self.decision is None) == (self.proposal is None):
            raise ValueError("a Pending carries exactly one of decision or proposal")

    @property
    def waiting_on(self) -> str:
        """The one line this pause is, whichever way the turn stopped."""
        if self.proposal is not None:
            return APPROVAL_OF.format(tool=self.proposal.tool)
        return self.decision.question if self.decision is not None else ""


class TurnPaused(Exception):
    """Not a failure: the turn stopped to ask, and picking it up again is the caller's.

    Deliberately not a `CoreError` — a shell that catches those to show a sentence must
    not show this one, because what belongs on the screen is the decision. A caller that
    handles neither hears about it loudly, which is the point: the alternative is a turn
    reported as answered with nothing in it.
    """

    def __init__(self, pending: Pending) -> None:
        """Carry the parked turn; what stopped it doubles as the exception's message."""
        super().__init__(pending.waiting_on)
        self.pending = pending
