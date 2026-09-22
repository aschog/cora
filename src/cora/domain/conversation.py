"""A conversation as a reader comes back to it: turns, and the threads holding them."""

from dataclasses import dataclass

from cora.domain.chat_result import ChatResult


@dataclass(frozen=True)
class Turn:
    """A question and what came back from it.

    The result is the agent's own — a turn is that result plus what was asked to get it,
    so nothing about an answer is restated here.
    """

    question: str
    result: ChatResult


@dataclass(frozen=True)
class Conversation:
    """A conversation, named by the question that opened it.

    A thread id is what the agent needs and nothing a reader could pick from a list.
    """

    thread_id: str
    opened_with: str
