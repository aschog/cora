"""What cora refuses before a turn starts, whatever the plugins add to it."""

from dataclasses import dataclass

from cora.domain.errors import InputRejectedError

MAX_INPUT_CHARS = 4000
"""What a question may run to. Beside the rule that enforces it, as the fact bound is
beside the tool it sizes."""


@dataclass(frozen=True)
class EmptyInputRule:
    """Nothing to answer is not a question."""

    def apply(self, user_input: str) -> None:
        """Refuse input that is empty or only whitespace.

        Raises:
            InputRejectedError: There is nothing there to answer.
        """
        if not user_input.strip():
            raise InputRejectedError("Please enter a question.")


@dataclass(frozen=True)
class MaxLengthRule:
    """A cap on one question, so a paste of a whole document is refused as input.

    Sized by the deployment rather than fixed here: `MAX_INPUT_CHARS` is what cora is
    assembled with.
    """

    max_chars: int

    def apply(self, user_input: str) -> None:
        """Refuse input longer than the cap, naming the cap.

        Raises:
            InputRejectedError: The message is over `max_chars` characters.
        """
        if len(user_input) > self.max_chars:
            raise InputRejectedError(
                f"Your message is too long — the limit is {self.max_chars} characters."
            )
