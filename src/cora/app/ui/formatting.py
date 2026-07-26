import json
from collections.abc import Sequence

from cora.core.ports.plugin import ToolResult


def numbered_sources(sources: Sequence[str]) -> list[str]:
    return [f"[{number}] {source}" for number, source in enumerate(sources, start=1)]


def format_tool_result(result: ToolResult) -> str:
    if result.error is not None:
        return result.error
    if isinstance(result.payload, str):
        return result.payload
    return json.dumps(result.payload, default=str)
