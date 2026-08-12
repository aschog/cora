import pytest

from cora.domain.errors import InputRejectedError
from cora.engine.validation import EmptyInputRule, MaxLengthRule


@pytest.mark.parametrize("user_input", ["", "   ", "\n\t "])
def test_empty_input_rule_rejects_blank_input(user_input: str) -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        EmptyInputRule().apply(user_input)

    assert excinfo.value.user_message


def test_empty_input_rule_accepts_real_input() -> None:
    EmptyInputRule().apply("How much protein per day?")


def test_max_length_rule_rejects_input_beyond_the_cap() -> None:
    with pytest.raises(InputRejectedError) as excinfo:
        MaxLengthRule(max_chars=10).apply("x" * 11)

    assert excinfo.value.user_message


def test_max_length_rule_accepts_input_within_the_cap() -> None:
    MaxLengthRule(max_chars=10).apply("x" * 10)
