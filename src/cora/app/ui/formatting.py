import json
from collections.abc import Sequence
from itertools import zip_longest
from typing import Any

from cora.core.ports.plugin import ToolResult
from cora.core.turn import Turn

ThreadEntry = dict[str, Any]


def numbered_sources(sources: Sequence[str]) -> list[str]:
    return [f"[{number}] {source}" for number, source in enumerate(sources, start=1)]


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


def thread_to_turns(thread: Sequence[ThreadEntry]) -> tuple[Turn, ...]:
    turns: list[Turn] = []
    for entry, follower in zip_longest(thread, thread[1:]):
        if "error" in entry:
            continue
        if entry["role"] == "user" and not _answers(follower):
            continue
        turns.append(Turn(role=entry["role"], text=entry["content"]))
    return tuple(turns)


def _answers(entry: ThreadEntry | None) -> bool:
    return entry is not None and entry["role"] == "assistant" and "error" not in entry
