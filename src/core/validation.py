from dataclasses import dataclass

from core.errors import InputRejectedError
from core.plugin import ValidationRule


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
