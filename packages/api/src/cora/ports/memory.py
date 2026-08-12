from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Fact:
    key: str
    text: str


class Memory(Protocol):
    """What the agent keeps about one user between sessions. Four verbs of intent
    rather than a key-value store: which user, and where the facts live, are the
    adapter's to know, so a slot bound to another technology — or to another
    user — changes nothing here. `recall` is ordered oldest first, and a `key`
    stays the same for the life of a fact, so whoever shows a fact can also
    offer to forget it."""

    def remember(self, text: str) -> None: ...

    def recall(self) -> tuple[Fact, ...]: ...

    def forget(self, key: str) -> None: ...

    def clear(self) -> None: ...
