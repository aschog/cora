import re
from dataclasses import dataclass
from typing import Protocol

from cora.domain.errors import InputRejectedError
from cora.ports.plugin import ValidationRule

MAX_INPUT_CHARS = 4000
"""What a question may run to. Beside the rule that enforces it, as the fact bound is
beside the tool it sizes."""


class InputValidator(Protocol):
    """Returns the input to use, or raises `InputRejectedError`. Beside the pipeline
    that implements it rather than beside one caller: the question and a remembered
    fact are both user input, and both go through it."""

    def validate(self, user_input: str) -> str: ...


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


@dataclass(frozen=True)
class PromptInjectionRule:
    """`refusal` is what the user reads. It is a field because the same rule guards two
    kinds of input — a question, and a note the user asked to be remembered — and a
    refusal quoted into the trace has to name the one it turned down."""

    refusal: str = (
        "Your message looks like an attempt to change my instructions. "
        "Please rephrase it as a genuine question."
    )

    def apply(self, user_input: str) -> None:
        normalized = " ".join(user_input.lower().split())
        if any(pattern.search(normalized) for pattern in _INJECTION_PATTERNS):
            raise InputRejectedError(self.refusal)


@dataclass(frozen=True)
class EmptyInputRule:
    refusal: str = "Please enter a question."

    def apply(self, user_input: str) -> None:
        if not user_input.strip():
            raise InputRejectedError(self.refusal)


@dataclass(frozen=True)
class MaxLengthRule:
    max_chars: int
    refusal: str = "Your message is too long — the limit is {limit} characters."

    def apply(self, user_input: str) -> None:
        if len(user_input) > self.max_chars:
            raise InputRejectedError(self.refusal.format(limit=self.max_chars))


@dataclass(frozen=True)
class ValidationPipeline:
    rules: tuple[ValidationRule, ...]

    def validate(self, user_input: str) -> str:
        for rule in self.rules:
            rule.apply(user_input)
        return user_input
