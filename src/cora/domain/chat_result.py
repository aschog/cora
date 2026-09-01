"""What one turn came to."""

from dataclasses import dataclass

from cora.domain.citations import Citation
from cora.domain.trace import TraceStep


@dataclass(frozen=True)
class ChatResult:
    """The answer to one question, with what it rested on and how it got there.

    `citations` are the ones the answer actually cites, not everything the turn
    retrieved, and `trace` covers this turn alone — a turn is reportable on its own or
    the report belongs to the conversation instead of to the answer.

    `scopes` are the fields it was answered in, which routing settles inside the turn:
    an unpinned conversation is answered in a field nothing outside the turn chose, so a
    reader shown documents and citations per field has no other way to know which.
    Plural because a caller may name several, as the state does — a reader that has to
    draw one field reads this as one field only when it names one.
    """

    answer: str
    citations: tuple[Citation, ...] = ()
    trace: tuple[TraceStep, ...] = ()
    scopes: tuple[str, ...] = ()
