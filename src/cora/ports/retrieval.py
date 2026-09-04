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

    The chunk carries its span and no text: what a search hands back to a caller is
    written by reading the file the span was measured in.
    """

    chunk: Chunk
    score: float


class Retriever(Protocol):
    """The index, one field at a time.

    A chunk goes in belonging to one upload — `file_hash` — and to one field, and comes
    back out stamped with both: a passage's offsets are only meaningful against the text
    that upload arrived as, and that text is kept under the field it was ingested into.
    Every method is asked within a field, so a passage of one is unreachable from
    another rather than merely filtered out of it.

    The words are not here. A chunk carries its span in, and comes back carrying the
    span alone — reading it is the document store's job, because that is where the one
    copy of the text is.

    Every method raises `RetrievalError` when the store cannot be reached.
    """

    def add(
        self,
        scope: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
        file_hash: str,
    ) -> None:
        """Index one upload's chunks in one field, each with the vector at its position.

        Args:
            scope: The field the upload was ingested into; it is what the chunks carry
                back out, and what every other method here is asked within.
            chunks: The upload's chunks, in the order they were cut.
            vectors: One per chunk, embedded by the same embedder a query will be.
            file_hash: The upload the chunks were cut from; it is what they carry back
                out, and what `contains` is asked about.
        """
        ...

    def query(
        self, scope: str, query_vector: list[float], k: int
    ) -> list[RetrievedChunk]:
        """The `k` closest passages in one field to a vector, closest first.

        Fewer only when the field holds fewer: the top of a ranking comes back whatever
        its scores.
        """
        ...

    def sources(self, scope: str) -> list[str]:
        """Every filename this field holds a passage from, each once.

        The name a document was uploaded under, which is what a reader recognises — two
        uploads of one name are one entry here.
        """
        ...

    def forget(self, scope: str, file_hash: str) -> None:
        """Drop every passage of one upload from one field.

        An upload nothing indexed is not an error: what was asked for is already true
        of it. The other uploads of that filename are left — the bytes name an upload,
        and a passage's offsets are only meaningful against the text it arrived as.
        """
        ...

    def uploads(self, scope: str, source: str) -> list[str]:
        """Every upload this field holds passages of under one filename.

        The mapping from what a listing shows to what a store forgets, which lives here
        because the passages carry both. A name nothing was uploaded under covers none.
        """
        ...

    def contains(self, scope: str, file_hash: str) -> bool:
        """Whether this upload has already been indexed in this field.

        The bytes name the upload, so this is what makes uploading the same file twice
        cost nothing — and a field is asked on its own, so a document already in one is
        still new to the next.
        """
        ...
