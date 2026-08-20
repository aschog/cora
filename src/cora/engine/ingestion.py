"""What a document has to be before it is indexed, and what it is refused for."""

from pathlib import Path
from typing import NamedTuple

from cora.domain.chunk import Chunk
from cora.domain.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from cora.engine.chunker import chunk_text
from cora.engine.cleaning import clean_text
from cora.ports.loading import Loaders

DEFAULT_MAX_BYTES = 10 * 1024 * 1024


class Ingested(NamedTuple):
    """The cleaned text and the chunks cut from it.

    Both, because a chunk's offset is a position in that text and means nothing without
    it.
    """

    text: str
    chunks: list[Chunk]


def ingest(
    data: bytes,
    filename: str,
    loaders: Loaders,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> Ingested:
    """Read a document and cut it up, or refuse it before anything is read.

    The refusals are ordered by what they cost: the extension is checked before the
    bytes are sized, and the size before a loader is run, so nothing expensive happens
    for a document that was never going to be accepted.

    Args:
        data: The uploaded bytes.
        filename: What the upload was called. Its extension picks the loader, and it is
            named in every refusal.
        loaders: Which extensions this deployment reads, and by what.
        max_bytes: The largest upload accepted.

    Raises:
        UnsupportedFileTypeError: No loader for that extension. The message lists the
            ones there are.
        FileTooLargeError: Over `max_bytes`. Nothing was read.
        EmptyDocumentError: The document was read and held no text — a scan, or a page
            of images.
        UnreadableFileError: The loader could not read the bytes as its format.
    """
    extension = Path(filename).suffix.lower()
    if extension not in loaders:
        raise UnsupportedFileTypeError(filename, loaders.keys())
    if len(data) > max_bytes:
        raise FileTooLargeError(filename)
    text = clean_text(loaders[extension](data, filename))
    if not text:
        raise EmptyDocumentError(filename)
    return Ingested(text=text, chunks=chunk_text(text, source=filename))
