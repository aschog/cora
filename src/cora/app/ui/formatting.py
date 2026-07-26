from collections.abc import Sequence


def numbered_sources(sources: Sequence[str]) -> list[str]:
    return [f"[{number}] {source}" for number, source in enumerate(sources, start=1)]
