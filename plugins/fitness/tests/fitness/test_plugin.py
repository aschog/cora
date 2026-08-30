from cora.plugins.fitness import INSTRUCTIONS, extend
from fakes import host_for


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


def test_it_registers_its_calculators_its_instructions_and_its_safety_rule() -> None:
    host = host_for("cora.plugins.fitness")

    extend(host)

    kinds = [entry.kind for entry in host.registered]
    assert kinds.count("tool") == 3
    assert kinds.count("instructions") == 1
    assert kinds.count("rule") == 1
