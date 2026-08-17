from cora.plugins.fitness import INSTRUCTIONS, PLUGIN, SCOPE


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the domain, the
    tools that must do its arithmetic, and where it stops."""
    instructions = INSTRUCTIONS.lower()

    assert "coach" in instructions
    assert "cite" in instructions
    assert "tool" in instructions
    assert "medical" in instructions


def test_the_instructions_carry_the_caution_the_rule_stopped_refusing_for() -> None:
    """`MedicalSafetyRule` lets a named condition through to be answered, so the caution
    that answer needs has to come from somewhere: only the model writes it, and only if
    the domain says so."""
    instructions = INSTRUCTIONS.lower()

    assert "condition" in instructions
    assert "doctor" in instructions


def test_the_scope_is_a_phrase_that_can_join_another() -> None:
    assert SCOPE.strip() == SCOPE
    assert "." not in SCOPE
    assert len(SCOPE.splitlines()) == 1


def test_the_bundle_offers_its_calculators_and_its_safety_rule() -> None:
    assert PLUGIN.name.strip()
    assert len(PLUGIN.tools) == 3
    assert PLUGIN.validation_rules
