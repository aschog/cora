from cora.engine.plugin_registry import load_plugin
from cora.plugins.fitness import INSTRUCTIONS, SCOPE
from cora.ports.plugin import Plugin


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the domain, the
    tools that must do its arithmetic, and where it stops."""
    instructions = INSTRUCTIONS.lower()

    assert "coach" in instructions
    assert "cite" in instructions
    assert "tool" in instructions
    assert "medical" in instructions


def test_the_scope_is_a_phrase_that_can_join_another() -> None:
    assert SCOPE.strip() == SCOPE
    assert "." not in SCOPE
    assert len(SCOPE.splitlines()) == 1


def test_load_plugin_returns_the_validated_bundle() -> None:
    plugin = load_plugin("cora.plugins.fitness")

    assert isinstance(plugin, Plugin)
    assert plugin.name.strip()
    assert len(plugin.tools) == 3
    assert plugin.validation_rules
