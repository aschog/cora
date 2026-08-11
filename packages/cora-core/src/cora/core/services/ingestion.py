from pathlib import Path

from cora.core.chunk import Chunk
from cora.core.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from cora.core.services.chunker import chunk_text
from cora.core.services.cleaning import clean_text
from cora.core.services.loaders import LOADERS

DEFAULT_MAX_BYTES = 10 * 1024 * 1024


def ingest(
    data: bytes,
    filename: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[Chunk]:
    extension = Path(filename).suffix.lower()
    if extension not in LOADERS:
        raise UnsupportedFileTypeError(filename, LOADERS.keys())
    if len(data) > max_bytes:
        raise FileTooLargeError(filename)
    text = clean_text(LOADERS[extension](data, filename))
    if not text:
        raise EmptyDocumentError(filename)
    return chunk_text(text, source=filename)
