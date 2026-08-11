from pathlib import Path

from cora.core.service_layer.chunker import chunk_text
from cora.core.service_layer.cleaning import clean_text
from cora.domain.chunk import Chunk
from cora.domain.errors import (
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from cora.ports.loading import Loaders

DEFAULT_MAX_BYTES = 10 * 1024 * 1024


def ingest(
    data: bytes,
    filename: str,
    loaders: Loaders,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[Chunk]:
    extension = Path(filename).suffix.lower()
    if extension not in loaders:
        raise UnsupportedFileTypeError(filename, loaders.keys())
    if len(data) > max_bytes:
        raise FileTooLargeError(filename)
    text = clean_text(loaders[extension](data, filename))
    if not text:
        raise EmptyDocumentError(filename)
    return chunk_text(text, source=filename)
