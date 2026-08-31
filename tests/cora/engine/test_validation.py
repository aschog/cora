import pytest

from cora.engine.validation import (
    MAX_INPUT_CHARS,
    refuse_nothing_to_answer,
    refuse_too_long,
)


@pytest.mark.parametrize("question", ["", "   ", "\n\t "])
def test_a_blank_question_is_refused(question: str) -> None:
    assert refuse_nothing_to_answer(question)


def test_a_real_question_is_let_through() -> None:
    assert refuse_nothing_to_answer("How much protein per day?") is None


def test_a_question_past_the_cap_is_refused_and_the_cap_is_named() -> None:
    refused = refuse_too_long("x" * (MAX_INPUT_CHARS + 1))

    assert refused is not None
    assert str(MAX_INPUT_CHARS) in refused


def test_a_question_at_the_cap_is_let_through() -> None:
    assert refuse_too_long("x" * MAX_INPUT_CHARS) is None
