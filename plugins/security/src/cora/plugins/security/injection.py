import re
from dataclasses import dataclass

from cora.domain.errors import InputRejectedError

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


@dataclass(frozen=True)
class PromptInjectionRule:
    def apply(self, user_input: str) -> None:
        normalized = " ".join(user_input.lower().split())
        if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
            raise InputRejectedError(REFUSAL)
