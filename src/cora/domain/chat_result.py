from dataclasses import dataclass

from cora.domain.citations import Citation
from cora.domain.trace import TraceStep


@dataclass(frozen=True)
class ChatResult:
    answer: str
    citations: tuple[Citation, ...] = ()
    trace: tuple[TraceStep, ...] = ()
