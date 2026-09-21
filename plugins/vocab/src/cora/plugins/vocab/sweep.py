"""One pass over a list: which of its words the reader has already produced.

What a session is when nothing is spacing it. SM2 answers "when does this word come
back", which is a question about weeks; a pass answers "is this word still to do
today", which is a question about the next ten minutes, and the two are kept apart
because they are kept for different lengths of time.

The words done rather than the order to put them in: picking at random from what is
left is a shuffle, and an order kept would be an order to keep in step with a list the
reader can edit mid-session.
"""

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sweep:
    """The words of this pass the reader has produced, each by the key it is held
    under. A word not in here is a word this pass has still to put."""

    done: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def of(cls, written: str | None) -> "Sweep":
        """The pass this text holds, or a fresh one where it holds none.

        Unreadable text reads as a fresh pass: what is lost is a few minutes of one
        session, and refusing would strand the reader with no way to clear it.
        """
        try:
            read = json.loads(written or "[]")
            return cls(frozenset(str(word) for word in read))
        except (ValueError, TypeError):
            return cls()

    def written(self) -> str:
        """This pass as the text to keep."""
        return json.dumps(sorted(self.done))

    def holds(self, word: str) -> bool:
        """Whether this word has already been produced in this pass."""
        return word in self.done

    def with_word(self, word: str) -> "Sweep":
        """This pass with one more word done, and no other touched."""
        return Sweep(self.done | {word})
