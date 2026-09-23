"""Where a plugin puts a document, so the field can be searched for it and cite it."""

from typing import Protocol

from cora.domain.chunk import Chunk


class Indexing(Protocol):
    """A document going into a field: its text kept, its passages embedded and indexed.

    One door for both writes, because a passage is only citable while the text it was
    cut from is there to open — whoever holds the two stores keeps them in that order,
    and a plugin handing over text and chunks cannot get it wrong. The embedding is the
    index's own: the same embedder a search uses, or the two sides never meet.

    Raises:
        DocumentStoreError: The text could not be kept.
        RetrievalError: The passages could not be indexed.
        EmbeddingError: The passages could not be embedded.
    """

    def add(
        self, scope: str, upload: str, filename: str, text: str, chunks: list[Chunk]
    ) -> bool:
        """Put one upload into one field, and say whether it was new there.

        Args:
            upload: What names the upload — the hash of its bytes, so the same file
                twice is one document and an edited one is another.
            filename: What it was uploaded as, which is what the field lists it by.
            text: The cleaned text every chunk's span was measured in.
            chunks: The passages, each carrying its text and its span in `text`.

        Returns:
            False where the field already held the upload, and nothing was added.
        """
        ...

    def holds(self, scope: str, upload: str) -> bool:
        """Whether this field already indexed this upload."""
        ...
