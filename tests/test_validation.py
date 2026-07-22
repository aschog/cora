from dataclasses import dataclass

import pytest

from docchat.errors import InputRejectedError
from docchat.validation import EmptyInputRule, MaxLengthRule, ValidationPipeline


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


def test_pipeline_runs_core_rules_before_plugin_rules() -> None:
    log: list[str] = []
    pipeline = ValidationPipeline(
        core_rules=(RecordingRule("core", log),),
        plugin_rules=(RecordingRule("plugin", log, rejects=True),),
    )

    with pytest.raises(InputRejectedError) as excinfo:
        pipeline.validate("hello")

    assert log == ["core", "plugin"]
    assert excinfo.value.user_message == "plugin says no"


def test_pipeline_raises_the_first_rejection_and_stops() -> None:
    log: list[str] = []
    pipeline = ValidationPipeline(
        core_rules=(RecordingRule("core", log, rejects=True),),
        plugin_rules=(RecordingRule("plugin", log, rejects=True),),
    )

    with pytest.raises(InputRejectedError) as excinfo:
        pipeline.validate("hello")

    assert log == ["core"]
    assert excinfo.value.user_message == "core says no"
