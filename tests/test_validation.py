import pytest

from docchat.errors import InputRejectedError
from docchat.validation import EmptyInputRule


@pytest.mark.parametrize("user_input", ["", "   ", "\n\t "])
def test_empty_input_rule_rejects_blank_input(user_input: str) -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        EmptyInputRule().apply(user_input)

    assert excinfo.value.user_message


def test_empty_input_rule_accepts_real_input() -> None:
    EmptyInputRule().apply("How much protein per day?")
