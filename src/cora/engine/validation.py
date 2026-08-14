from dataclasses import dataclass

from cora.domain.errors import InputRejectedError

MAX_INPUT_CHARS = 4000
"""What a question may run to. Beside the rule that enforces it, as the fact bound is
beside the tool it sizes."""


@dataclass(frozen=True)
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
