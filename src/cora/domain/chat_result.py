from dataclasses import dataclass

from cora.domain.citations import Source
from cora.domain.trace import TraceStep


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[Source, ...] = ()
    trace: tuple[TraceStep, ...] = ()
