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
    """The cleaned text and the chunks cut from it. Both, because a chunk's offset is a
    position in that text and means nothing without it."""

    text: str
    chunks: list[Chunk]


def ingest(
    data: bytes,
    filename: str,
    loaders: Loaders,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> Ingested:
    extension = Path(filename).suffix.lower()
    if extension not in loaders:
        raise UnsupportedFileTypeError(filename, loaders.keys())
    if len(data) > max_bytes:
        raise FileTooLargeError(filename)
    text = clean_text(loaders[extension](data, filename))
    if not text:
        raise EmptyDocumentError(filename)
    return Ingested(text=text, chunks=chunk_text(text, source=filename))
