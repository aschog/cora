from collections.abc import Sequence

from cora.core.citations import Source
from cora.core.trace import TraceStep

DETAIL_CAP = 800


def step_lines(step: TraceStep) -> list[str]:
    headline = f"⚠️ **{step.summary}**" if step.failed else f"**{step.summary}**"
    if not step.detail or step.detail in step.summary:
        return [headline]
    return [headline, f"```text\n{_capped(step.detail)}\n```"]


def _capped(detail: str) -> str:
    return detail if len(detail) <= DETAIL_CAP else f"{detail[:DETAIL_CAP]}…"


def numbered_sources(sources: Sequence[Source]) -> list[str]:
    return [f"[{source.number}] {source.name}" for source in sources]


def ingest_message(filename: str, chunks: int) -> str:
    if not chunks:
        return f"{filename} is already in your knowledge base."
    unit = "chunk" if chunks == 1 else "chunks"
    return f"Added {filename} — {chunks} {unit}."
