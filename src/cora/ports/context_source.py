"""Where the agent's search tool reads from, and a plugin reads its field whole."""

from dataclasses import dataclass
from typing import Protocol

from cora.ports.retrieval import RetrievedChunk


@dataclass(frozen=True)
class Document:
    """One document a field holds, as a plugin reads it.

    `name` is what it was uploaded under and what the rail shows, `text` is the cleaned
    text the store kept — what a citation into it opens — and `scope` is the field it
    came from, for work running in more than one.
    """

    name: str
    text: str
    scope: str


class ContextSource(Protocol):
    """The passages behind a question, ranked, and the documents behind the passages.

    Narrower than `Retriever` on purpose: the tool asks a question and is handed
    passages, and nothing about how they are indexed reaches it.
    """

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        """The `k` best passages for a question, best first.

        Fewer than `k` come back only when the store holds fewer: the top of a ranking
        is returned whatever its scores, so an empty list means nothing has been
        indexed rather than a question the documents do not answer.

        Raises:
            RetrievalError: The store could not be searched.
        """
        ...

    def all(self) -> list[Document]:
        """Every document in the fields the work is running in.

        The names in the order first uploaded, and the uploads of one name together,
        oldest first: two uploads of one name are two documents. One whose text is gone
        is left out, as a passage of it would be.

        Raises:
            RetrievalError: The store could not be read.
        """
        ...
