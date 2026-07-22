from docchat.errors import InputRejectedError


class EmptyInputRule:
    def apply(self, user_input: str) -> None:
        if not user_input.strip():
            raise InputRejectedError("Please enter a question.")
