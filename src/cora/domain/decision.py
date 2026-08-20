from dataclasses import dataclass


@dataclass(frozen=True)
class Option:
    """One way the run could go. `note` is where the value came from, which is what
    makes two of these tellable apart by whoever has to choose."""

    label: str
    note: str = ""


@dataclass(frozen=True)
class Decision:
    """What cora stopped to have settled, in its own words. The options are the
    model's rather than a rule's: ranking two remembered values against each other is
    reading them and where each came from, which no mark on a tool can do."""

    question: str
    options: tuple[Option, ...] = ()
    decline: str = ""


@dataclass(frozen=True)
class Pending:
    """A turn parked on a decision. `asked` is the question the turn opened with, kept
    beside the decision because a paused turn is in no store yet and the page has to
    draw the card under the question that raised it."""

    asked: str
    decision: Decision


class TurnPaused(Exception):
    """Not a failure: the turn stopped to ask, and picking it up again is the caller's
    to do. Deliberately not a `CoreError` — a shell that catches those to show a
    sentence must not show this one, because what belongs on the screen is the
    decision. A caller that handles neither hears about it loudly, which is the point:
    the alternative is a turn reported as answered with nothing in it."""

    def __init__(self, pending: Pending) -> None:
        super().__init__(pending.decision.question)
        self.pending = pending
