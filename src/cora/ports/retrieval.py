"""The index a passage is put into and searched out of."""

from dataclasses import dataclass
from typing import Protocol

from cora.domain.chunk import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    """A passage the index handed back, and how well it matched.

    `score` compares hits of one search and nothing else: higher is a closer match, and
    the range is the store's own business — an absolute value carries no meaning a
    threshold could be written against.
    """

    chunk: Chunk
    score: float


class Retriever(Protocol):
    """The index.

    A chunk goes in belonging to one upload — `file_hash` — and comes back out stamped
    with it, because a passage's offsets are only meaningful against the text that
    upload arrived as, and the store is the only thing that still knows which one that
    was.

    Every method raises `RetrievalError` when the store cannot be reached.
    """

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        """Index one upload's chunks under it, each with the vector at its position.

        Args:
            chunks: The upload's chunks, in the order they were cut.
            vectors: One per chunk, embedded by the same embedder a query will be.
            file_hash: The upload the chunks were cut from; it is what they carry back
                out, and what `contains` is asked about.
        """
        ...

    def query(self, query_vector: list[float], k: int) -> list[RetrievedChunk]:
        """The `k` closest passages to a vector, closest first.

        Fewer only when the index holds fewer: the top of a ranking comes back whatever
        its scores.
        """
        ...

    def sources(self) -> list[str]:
        """Every filename the index holds a passage from, each once.

        The name a document was uploaded under, which is what a reader recognises — two
        uploads of one name are one entry here.
        """
        ...

    def contains(self, file_hash: str) -> bool:
        """Whether this upload has already been indexed.

        The bytes name the upload, so this is what makes uploading the same file twice
        cost nothing.
        """
        ...
