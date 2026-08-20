"""How a document's bytes become text, and which formats a deployment reads."""

from collections.abc import Mapping
from typing import Protocol


class Loader(Protocol):
    """Turns one format's bytes into its text."""

    def __call__(self, data: bytes, filename: str) -> str:
        """The document's text, as the format gives it up.

        Args:
            data: The uploaded bytes, whole.
            filename: What the upload was called — carried so a failure can name it,
                never read to decide the format.

        Raises:
            UnreadableFileError: The bytes are not that format, or hold no text this
                loader can reach.
        """
        ...


Loaders = Mapping[str, Loader]
"""Which extensions can be read, and by what. Injected rather than fixed in core: the
formats a deployment accepts are its choice, and adding one is a new entry here
instead of an edit inside ingestion."""
