import re

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(ignore|disregard|forget|override)\b.{0,40}"
        r"\b(previous|above|prior|earlier|system)\b.{0,30}(instruction|prompt)"
    ),
    re.compile(
        r"(reveal|show|print|repeat|expose|tell me)\b.{0,40}"
        r"\b(your (system )?(prompt|instructions)|system prompt)"
    ),
)


REFUSAL = (
    "Your message looks like an attempt to change my instructions. "
    "Please rephrase it as a genuine question."
)


def refuse_injection(question: str) -> str | None:
    normalized = " ".join(question.lower().split())
    if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
        return REFUSAL
    return None
