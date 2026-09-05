"""How a run stops to put a card to the user, and what a shell that cannot answers."""

from collections.abc import Callable

from cora.domain.card import Answer, Asks

Answered = Callable[[Asks], Answer | None]
"""How a step stops the run and waits. It travels *in*, like `TextSink`, because only
whatever is driving the graph can park a run and pick it up again — the engine puts
what it stopped on, and is handed back the action taken and what was written, or
nothing at all if the user declined.

One port over every way a turn can stop. What parks a run is the card, and a decision,
a proposal and a form all have one: a second port would be the same mechanism written
twice, and a third would be it written three times."""


def declined(_: Asks) -> None:
    """Decline every card the moment it is put.

    The answer of a caller that cannot stop and ask, so a shell with no card to draw
    still gets its turn — and changes nothing outside cora, because a proposal put to
    this one is refused. Every slot that takes an `Answered` defaults to it, which is
    what keeps a run that cannot be interrupted from hanging on one.
    """
