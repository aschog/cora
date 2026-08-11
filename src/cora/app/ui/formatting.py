import re
from collections.abc import Sequence

from cora.core.citations import Source
from cora.core.trace import TraceStep

DETAIL_CAP = 800


def step_line(step: TraceStep) -> str:
    """A summary names the tool the model asked for, so the model — and a
    document telling it what to ask for — writes part of this line. Only the
    marks cora adds are markdown; the rest is flattened to one plain line."""
    headline = _one_plain_line(step.summary)
    return f"⚠️ **{headline}**" if step.failed else f"**{headline}**"


def _one_plain_line(text: str) -> str:
    """Escapes what can build structure — a fence, bold, a link — and leaves what
    cannot, so a snake_case tool name still reads as itself."""
    collapsed = " ".join(text.split())
    return re.sub(r"([\\`*\[\]])", r"\\\1", collapsed)


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
