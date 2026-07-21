from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    index: int
    offset: int
    score: float
