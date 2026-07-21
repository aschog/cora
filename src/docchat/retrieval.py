from dataclasses import dataclass

from docchat.chunk import Chunk


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float
