from cora.plugins.security import PLUGIN


def test_the_bundle_carries_a_rule_and_nothing_else() -> None:
    """A guard, not a domain: the screen adds no persona and no tools, so loading it
    does not tell cora what it is for."""
    assert PLUGIN.name.strip()
    assert PLUGIN.instructions == ""
    assert PLUGIN.tools == ()
    assert len(PLUGIN.validation_rules) == 1
