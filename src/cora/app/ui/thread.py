from collections.abc import Sequence
from itertools import zip_longest
from typing import Any

from cora.core.turn import Turn

ThreadEntry = dict[str, Any]


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
