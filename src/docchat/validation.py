from dataclasses import dataclass

from docchat.errors import InputRejectedError


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
