from cora.plugins.fitness import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import HANDLER, SCREENING, TOOL
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the domain, the
    tools that must do its arithmetic, and where it stops."""
    instructions = INSTRUCTIONS.lower()

    assert "coach" in instructions
    assert "cite" in instructions
    assert "tool" in instructions
    assert "medical" in instructions


def test_the_instructions_carry_the_caution_the_screen_stopped_refusing_for() -> None:
    """`refuse_medical` lets a named condition through to be answered, so the caution
    that answer needs has to come from somewhere: only the model writes it, and only if
    the domain says so."""
    instructions = INSTRUCTIONS.lower()

    assert "condition" in instructions
    assert "doctor" in instructions


def test_the_coaching_is_scoped_and_the_medical_screen_is_not() -> None:
    """One plugin under two lifetimes: the persona and the calculators belong to a turn
    asking as a coach, and the medical filter holds wherever the question was asked."""
    host = host_for("cora.plugins.fitness")

    extend(host)

    under = [(entry.kind, entry.scope) for entry in host.registered]
    assert under.count((TOOL, SCOPE)) == 3
    assert under.count((SAYS, SCOPE)) == 1
    assert under.count((HANDLER, None)) == 1
    [screen] = [entry for entry in host.registered if entry.kind == HANDLER]
    assert screen.value.event == SCREENING
