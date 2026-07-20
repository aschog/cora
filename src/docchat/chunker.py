from docchat.chunk import Chunk

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 150


def chunk_text(
    text: str,
    *,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [Chunk(text=text, source=source, index=0, offset=0)]
    raise NotImplementedError
