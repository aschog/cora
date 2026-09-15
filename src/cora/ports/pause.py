"""How a run stops to put a card to the user, and what a shell that cannot answers."""

from collections.abc import Callable

from cora.domain.card import Answer, Asks

Answered = Callable[[Asks], Answer | None]


def declined(_: Asks) -> None:
    """Decline every card the moment it is put.

    The answer of a caller that cannot stop and ask, so a shell with no card to draw
    still gets its turn — and changes nothing outside cora, because a proposal put to
    this one is refused. Every slot that takes an `Answered` defaults to it, which is
    what keeps a run that cannot be interrupted from hanging on one.
    """
