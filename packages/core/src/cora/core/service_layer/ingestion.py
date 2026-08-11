from pathlib import Path

from cora.core.domain.chunk import Chunk
from cora.core.domain.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from cora.core.service_layer.chunker import chunk_text
from cora.core.service_layer.cleaning import clean_text
from cora.core.service_layer.loaders import LOADERS

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
