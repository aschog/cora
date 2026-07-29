import json
from collections.abc import Sequence

from cora.core.ports.plugin import ToolResult
from cora.core.services.chat_engine import Source


def numbered_sources(sources: Sequence[Source]) -> list[str]:
    return [f"[{source.number}] {source.name}" for source in sources]


def ingest_message(filename: str, chunks: int) -> str:
    if not chunks:
        return f"{filename} is already in your knowledge base."
    unit = "chunk" if chunks == 1 else "chunks"
    return f"Added {filename} — {chunks} {unit}."


def format_tool_result(result: ToolResult) -> str:
    if result.error is not None:
        return result.error
    if isinstance(result.payload, str):
        return result.payload
    return json.dumps(result.payload, default=str)
