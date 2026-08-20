"""What the agent keeps about a user between sessions."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Fact:
    """One remembered thing, and the name to forget it by.

    `key` is the store's, not the user's: it stays the same for the life of the fact,
    so whoever shows a fact can offer to forget that one and no other.
    """

    key: str
    text: str


class Memory(Protocol):
    """What the agent keeps about one user between sessions.

    Four verbs of intent rather than a key-value store: which user, and where the facts
    live, are the adapter's to know, so a slot bound to another technology — or to
    another user — changes nothing here.
    """

    def remember(self, text: str) -> None:
        """Keep a fact. Nothing is replaced, so remembering twice is two facts.

        Raises:
            MemoryStoreError: The fact could not be written.
        """
        ...

    def recall(self) -> tuple[Fact, ...]:
        """The user's facts, oldest first.

        An adapter may hand back a window rather than everything it holds — a fact just
        learned is the one a turn is likeliest to need — so this is what the agent can
        see, not proof of what is kept.

        Raises:
            MemoryStoreError: The facts could not be read.
        """
        ...

    def forget(self, key: str) -> None:
        """Drop the fact a `key` names. A key nothing is kept under is not an error.

        Raises:
            MemoryStoreError: The fact could not be dropped.
        """
        ...

    def clear(self) -> None:
        """Forget everything kept for this user, window or no window.

        Raises:
            MemoryStoreError: The facts could not be dropped.
        """
        ...
