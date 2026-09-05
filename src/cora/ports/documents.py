"""Where the text a citation opens onto is kept."""

from typing import Protocol


class Documents(Protocol):
    """The text a citation's offsets point into, kept under the field that owns it.

    It is the *cleaned* text ingestion chunked, not the uploaded bytes: an offset means
    nothing against anything else.

    Keyed by the scope and then by the upload rather than by the filename, because a
    filename is not a promise: the same name uploaded twice is two documents, and a span
    measured in the first would silently read the second. A scope reads its own and no
    other's, which is what keeps one field's passage out of another field's answer.
    """

    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
        """Keep an upload's cleaned text under its scope, named for the file it was.

        Keeping the same upload twice is not an error: the bytes name the upload, so
        the second text is the first one.

        Args:
            filename: What the upload was called. It names the file this text is kept
                as, so a person reading the directory can tell what they are looking at.

        Raises:
            DocumentStoreError: The text could not be written, or the scope is not a
                name this store can keep a document under.
        """
        ...

    def forget(self, scope: str, upload: str) -> None:
        """Drop the text kept for one upload in this scope.

        An upload nothing was kept for is not an error: the index is dropped first, so
        this may be asked about a passage whose text was never written. Nothing outside
        the scope's own directory is touched, however the scope is named — a scope this
        store could not keep a document under drops nothing and says nothing, because
        there is nothing of it here to drop.

        Raises:
            DocumentStoreError: The text could not be dropped.
        """
        ...

    def read(self, scope: str, upload: str) -> str | None:
        """The text kept for an upload in this scope, or nothing if none was.

        Nothing is the answer for an upload kept under another scope, and for one
        indexed before its text was kept — a citation into it can be read as a passage
        but not opened as a document.

        Raises:
            DocumentStoreError: The store could not be read.
        """
        ...
