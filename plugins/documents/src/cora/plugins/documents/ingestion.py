import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NamedTuple

from cora.domain.chunk import Chunk

from .chunker import chunk_text

Loader = Callable[[bytes, str], str]
Loaders = Mapping[str, Loader]

DEFAULT_MAX_BYTES = 10 * 1024 * 1024
UNSUPPORTED = "unsupported file type (supported: {formats})."
TOO_LARGE = "the file is too large."
EMPTY = "the document has no readable text."
UNREADABLE = "the file is corrupted or unreadable."

_BLANK_LINES = re.compile(r"\n{3,}")


class Refused(Exception):
    """An upload this plugin will not index, in the sentence the reader is told.

    Its own rather than one of cora's: what cora does with a refused upload is
    cora's, and what makes a document unreadable is this plugin's alone to say.
    """

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(f"Could not process '{filename}': {reason}")
        self.said = str(self)


class Ingested(NamedTuple):
    text: str
    chunks: list[Chunk]


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def reads(filename: str, loaders: Loaders) -> bool:
    """Whether this deployment has a loader for what the filename says the file is."""
    return Path(filename).suffix.lower() in loaders


def ingest(
    data: bytes,
    filename: str,
    loaders: Loaders,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> Ingested:
    """Read a document and cut it up, or refuse it before anything is read.

    The refusals are ordered by what they cost: the extension is checked before the
    bytes are sized, and the size before a loader is run.

    Raises:
        Refused: No loader for that extension, over `max_bytes`, no text once read, or
            bytes the loader could not read as its format. The sentence names the file.
    """
    extension = Path(filename).suffix.lower()
    if extension not in loaders:
        formats = ", ".join(sorted(loaders))
        raise Refused(filename, UNSUPPORTED.format(formats=formats))
    if len(data) > max_bytes:
        raise Refused(filename, TOO_LARGE)
    text = clean_text(loaders[extension](data, filename))
    if not text:
        raise Refused(filename, EMPTY)
    return Ingested(text=text, chunks=chunk_text(text, source=filename))
