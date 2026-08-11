from collections.abc import Sequence

from cora.core.domain.citations import Source
from cora.core.domain.trace import TraceStep

DETAIL_CAP = 800
SUMMARY_CAP = 200


def step_text(step: TraceStep) -> str:
    """The whole step as plain text, because the caller renders it as code: a
    summary names the tool the model asked for, and a document can tell it what
    to ask for, so nothing here may be markdown."""
    head = _capped(" ".join(step.summary.split()), SUMMARY_CAP)
    if step.failed:
        head = f"⚠️ {head}"
    if not step.detail or step.detail in step.summary:
        return head
    return f"{head}\n{_capped(step.detail, DETAIL_CAP)}"


def _capped(text: str, cap: int) -> str:
    return text if len(text) <= cap else f"{text[:cap]}…"


def numbered_sources(sources: Sequence[Source]) -> list[str]:
    return [f"[{source.number}] {source.name}" for source in sources]


def ingest_message(filename: str, chunks: int) -> str:
    if not chunks:
        return f"{filename} is already in your knowledge base."
    unit = "chunk" if chunks == 1 else "chunks"
    return f"Added {filename} — {chunks} {unit}."
