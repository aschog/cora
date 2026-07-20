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
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [Chunk(text=text, source=source, index=0, offset=0)]
    return [
        Chunk(
            text=text[start : start + chunk_size], source=source, index=i, offset=start
        )
        for i, start in enumerate(range(0, len(text), chunk_size))
    ]
