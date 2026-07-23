from docchat.plugin import Plugin
from docchat.plugin_registry import load_plugin
from docchat_plugins.fitness import SYSTEM_PROMPT


def test_system_prompt_sets_persona_and_load_bearing_instructions() -> None:
    prompt = SYSTEM_PROMPT.lower()

    assert prompt.strip()
    assert "coach" in prompt
    assert "cite" in prompt or "source" in prompt
    assert "tool" in prompt
    assert "medical" in prompt


def test_load_plugin_returns_the_validated_bundle() -> None:
    plugin = load_plugin("docchat_plugins.fitness")

    assert isinstance(plugin, Plugin)
    assert len(plugin.tools) == 3
    assert plugin.validation_rules
    assert plugin.seed_docs
