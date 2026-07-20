import os

from docchat.chunk import Chunk
from docchat.chunker import chunk_text
from docchat.cleaning import clean_text
from docchat.errors import FileTooLargeError, UnsupportedFileTypeError
from docchat.loaders import LOADERS

DEFAULT_MAX_BYTES = 10 * 1024 * 1024


def ingest(
    data: bytes,
    filename: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[Chunk]:
    extension = os.path.splitext(filename)[1].lower()
    if extension not in LOADERS:
        raise UnsupportedFileTypeError(filename, LOADERS.keys())
    if len(data) > max_bytes:
        raise FileTooLargeError(filename)
    text = clean_text(LOADERS[extension](data, filename))
    return chunk_text(text, source=filename)
