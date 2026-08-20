"""Where the text a citation opens onto is kept."""

from typing import Protocol


class Documents(Protocol):
    """The text a citation's offsets point into, kept under the upload it was.

    It is the *cleaned* text ingestion chunked, not the uploaded bytes: an offset means
    nothing against anything else.

    Keyed by the upload rather than by the filename, because a filename is not a
    promise: the same name uploaded twice is two documents, and a span measured in the
    first would silently read the second.
    """

    def keep(self, upload: str, text: str) -> None:
        """Keep an upload's cleaned text under the upload's own name.

        Keeping the same upload twice is not an error: the bytes name the upload, so
        the second text is the first one.

        Raises:
            DocumentStoreError: The text could not be written.
        """
        ...

    def read(self, upload: str) -> str | None:
        """The text kept for an upload, or nothing if none was ever kept for it.

        Nothing is the answer for an upload indexed before its text was kept — a
        citation into it can be read as a passage but not opened as a document.

        Raises:
            DocumentStoreError: The store could not be read.
        """
        ...
