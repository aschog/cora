import os

from docchat.chunk import Chunk
from docchat.chunker import chunk_text
from docchat.cleaning import clean_text
from docchat.errors import UnsupportedFileTypeError
from docchat.loaders import LOADERS


def ingest(data: bytes, filename: str) -> list[Chunk]:
    extension = os.path.splitext(filename)[1].lower()
    if extension not in LOADERS:
        raise UnsupportedFileTypeError(filename, LOADERS.keys())
    text = clean_text(LOADERS[extension](data, filename))
    return chunk_text(text, source=filename)
