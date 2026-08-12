import re
from dataclasses import dataclass

from cora.domain.errors import InputRejectedError
from cora.ports.plugin import ValidationRule

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


class PromptInjectionRule:
    def apply(self, user_input: str) -> None:
        normalized = " ".join(user_input.lower().split())
        if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
            raise InputRejectedError(
                "Your message looks like an attempt to change my instructions. "
                "Please rephrase it as a genuine question."
            )


class EmptyInputRule:
    def apply(self, user_input: str) -> None:
        if not user_input.strip():
            raise InputRejectedError("Please enter a question.")


@dataclass(frozen=True)
class MaxLengthRule:
    max_chars: int

    def apply(self, user_input: str) -> None:
        if len(user_input) > self.max_chars:
            raise InputRejectedError(
                f"Your message is too long — the limit is {self.max_chars} characters."
            )


@dataclass(frozen=True)
class ValidationPipeline:
    core_rules: tuple[ValidationRule, ...]
    plugin_rules: tuple[ValidationRule, ...]

    def validate(self, user_input: str) -> str:
        for rule in self.core_rules + self.plugin_rules:
            rule.apply(user_input)
        return user_input
