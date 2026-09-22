"""Where a conversation outlives the process that held it."""

from typing import Protocol

from cora.domain.conversation import Conversation, Turn


class Conversations(Protocol):
    """Every turn of every conversation, so one can be reopened later.

    The agent's own memory of a thread is the runner's business — this is what a reader
    comes back to: what was asked, what was answered, and what that answer rested on.
    """

    def record(self, thread_id: str, turn: Turn) -> None:
        """Add a finished turn to the end of its thread.

        A turn is appended, never merged: the same question asked twice is two turns,
        and nothing already recorded is rewritten.
        """
        ...

    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        """A thread's turns, oldest first — the order the conversation was taken in.

        A thread nothing was ever recorded under is empty rather than missing.
        """
        ...

    def forget(self, thread_id: str) -> None:
        """Drop every turn of one thread, leaving the others alone.

        A thread nothing was recorded under is not an error: what was asked for is
        already true of it.

        Raises:
            ConversationStoreError: The turns could not be dropped.
        """
        ...

    def opened(self) -> tuple[Conversation, ...]:
        """Every thread that has recorded a turn, newest first.

        A list of conversations is read from the top. A thread that has answered
        nothing appears in no list, so a conversation exists here from its first
        recorded turn.
        """
        ...
