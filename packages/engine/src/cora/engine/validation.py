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
