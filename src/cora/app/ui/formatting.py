from collections.abc import Sequence

from cora.core.citations import Source
from cora.core.trace import TraceStep

DETAIL_CAP = 800


def step_line(step: TraceStep) -> str:
    return f"⚠️ **{step.summary}**" if step.failed else f"**{step.summary}**"


def step_detail(step: TraceStep) -> str:
    """Returned as plain text, never wrapped in markdown: the caller renders it
    as code, so a document carrying its own fence cannot forge trace lines."""
    if not step.detail or step.detail in step.summary:
        return ""
    return _capped(step.detail)


def _capped(detail: str) -> str:
    return detail if len(detail) <= DETAIL_CAP else f"{detail[:DETAIL_CAP]}…"


def numbered_sources(sources: Sequence[Source]) -> list[str]:
    return [f"[{source.number}] {source.name}" for source in sources]


def ingest_message(filename: str, chunks: int) -> str:
    if not chunks:
        return f"{filename} is already in your knowledge base."
    unit = "chunk" if chunks == 1 else "chunks"
    return f"Added {filename} — {chunks} {unit}."
