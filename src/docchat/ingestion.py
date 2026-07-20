import os

from docchat.chunk import Chunk
from docchat.errors import UnsupportedFileTypeError
from docchat.loaders import LOADERS


def ingest(data: bytes, filename: str) -> list[Chunk]:
    extension = os.path.splitext(filename)[1].lower()
    if extension not in LOADERS:
        raise UnsupportedFileTypeError(filename, LOADERS.keys())
    raise NotImplementedError
