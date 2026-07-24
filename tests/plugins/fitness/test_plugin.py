import pytest

from core.errors import InputRejectedError
from core.ports.plugin import Plugin
from core.services.plugin_registry import load_plugin
from core.services.validation import EmptyInputRule, MaxLengthRule, ValidationPipeline
from plugins.fitness import PLUGIN, SYSTEM_PROMPT


def test_system_prompt_sets_persona_and_load_bearing_instructions() -> None:
    prompt = SYSTEM_PROMPT.lower()

    assert prompt.strip()
    assert "coach" in prompt
    assert "cite" in prompt or "source" in prompt
    assert "tool" in prompt
    assert "medical" in prompt


def test_load_plugin_returns_the_validated_bundle() -> None:
    plugin = load_plugin("plugins.fitness")

    assert isinstance(plugin, Plugin)
    assert len(plugin.tools) == 3
    assert plugin.validation_rules
    assert plugin.seed_docs


def _pipeline() -> ValidationPipeline:
    return ValidationPipeline(
        core_rules=(EmptyInputRule(), MaxLengthRule(max_chars=1000)),
        plugin_rules=PLUGIN.validation_rules,
    )


def test_plugin_rule_redirects_a_dosage_question_through_the_pipeline() -> None:
    with pytest.raises(InputRejectedError):
        _pipeline().validate("What steroid dosage should I take?")


def test_pipeline_passes_a_benign_question_unchanged() -> None:
    question = "How much protein should I eat to build muscle?"

    assert _pipeline().validate(question) == question
