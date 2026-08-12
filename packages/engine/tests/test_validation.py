from dataclasses import dataclass

import pytest

from cora.domain.errors import InputRejectedError
from cora.engine.validation import EmptyInputRule, MaxLengthRule, ValidationPipeline


@dataclass
class RecordingRule:
    name: str
    log: list[str]
    rejects: bool = False

    def apply(self, user_input: str) -> None:
        self.log.append(self.name)
        if self.rejects:
            raise InputRejectedError(f"{self.name} says no")


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


def make_pipeline(
    first_rejects: bool = False, second_rejects: bool = False
) -> tuple[ValidationPipeline, list[str]]:
    log: list[str] = []
    pipeline = ValidationPipeline(
        (
            RecordingRule("first", log, rejects=first_rejects),
            RecordingRule("second", log, rejects=second_rejects),
        )
    )
    return pipeline, log


def test_pipeline_raises_the_first_rejection_and_stops() -> None:
    pipeline, log = make_pipeline(first_rejects=True, second_rejects=True)

    with pytest.raises(InputRejectedError) as excinfo:
        pipeline.validate("hello")

    assert log == ["first"]
    assert excinfo.value.user_message == "first says no"


def test_pipeline_returns_the_input_unchanged_when_every_rule_accepts() -> None:
    pipeline, _ = make_pipeline()

    assert pipeline.validate("  keep me as I am  ") == "  keep me as I am  "
