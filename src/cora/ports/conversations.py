from typing import Protocol

from cora.domain.conversation import Session, Turn


class Conversations(Protocol):
    """Every turn of every conversation, so one can be reopened after the process that
    ran it has gone. The agent's own memory of a thread is the runner's business — this
    is what a reader comes back to: what was asked, what was answered, and what that
    answer rested on.

    `turns` is ordered as the conversation was taken, oldest first; `sessions` is
    ordered newest first, because a list of conversations is read from the top."""

    def record(self, thread_id: str, turn: Turn) -> None: ...

    def turns(self, thread_id: str) -> tuple[Turn, ...]: ...

    def sessions(self) -> tuple[Session, ...]: ...
