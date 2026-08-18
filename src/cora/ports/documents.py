from typing import Protocol


class Documents(Protocol):
    """The text a citation's offsets point into, kept under the upload it was. It is the
    *cleaned* text ingestion chunked, not the uploaded bytes: an offset means nothing
    against anything else.

    Keyed by the upload rather than by the filename, because a filename is not a
    promise: the same name uploaded twice is two documents, and a span measured in the
    first would silently read the second."""

    def keep(self, upload: str, text: str) -> None: ...

    def read(self, upload: str) -> str | None: ...
