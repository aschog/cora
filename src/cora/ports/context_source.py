"""Where the agent's search tool reads from."""

from typing import Protocol

from cora.ports.retrieval import RetrievedChunk


class ContextSource(Protocol):
    """The passages behind a question, ranked.

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
