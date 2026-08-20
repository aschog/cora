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
    """

    answer: str
    citations: tuple[Citation, ...] = ()
    trace: tuple[TraceStep, ...] = ()
