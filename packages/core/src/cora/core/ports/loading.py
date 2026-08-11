from collections.abc import Mapping
from typing import Protocol


class Loader(Protocol):
    """Turns a document's bytes into its text, or raises `UnreadableFileError`."""

    def __call__(self, data: bytes, filename: str) -> str: ...


Loaders = Mapping[str, Loader]
"""Which extensions can be read, and by what. Injected rather than fixed in core: the
formats a deployment accepts are its choice, and adding one is a new entry here
instead of an edit inside ingestion."""
