"""What cora stops a turn to ask, and how a parked turn is carried."""

from dataclasses import dataclass

from cora.domain.card import ActionOffered, Card

NO_OPTION = "None of them"
DECLINED = "You chose none of them."


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

    @property
    def card(self) -> Card:
        """This, as the reader is shown it: no fields, and one action per option.

        Nothing to fill in, because a decision is picking between values cora already
        found. The way out is an action like the others, so a card is left the same way
        whichever action leaves it.
        """
        return Card(
            prompt=self.question,
            actions=(
                *(
                    ActionOffered(
                        label=option.label, answer=option.label, note=option.note
                    )
                    for option in self.options
                ),
                ActionOffered(
                    label=self.decline or NO_OPTION, answer=None, settled=DECLINED
                ),
            ),
        )


@dataclass(frozen=True)
class Pending:
    """A turn parked on something the user has to settle, as the reader is shown it.

    `asked` is the question the turn opened with, kept beside the card because a paused
    turn is in no store yet and the page has to draw the card under the question that
    raised it.

    One card, whatever stopped the turn. What a decision, a proposal and a form have in
    common is all the page needs, and a shape naming which of them it was would make the
    page ask.
    """

    asked: str
    card: Card


class TurnPaused(Exception):
    """Not a failure: the turn stopped to ask, and picking it up again is the caller's.

    Deliberately not a `CoreError` — a shell that catches those to show a sentence must
    not show this one, because what belongs on the screen is the card. A caller that
    handles neither hears about it loudly, which is the point: the alternative is a turn
    reported as answered with nothing in it.
    """

    def __init__(self, pending: Pending) -> None:
        """Carry the parked turn; the card's prompt is the exception's message."""
        super().__init__(pending.card.prompt)
        self.pending = pending
