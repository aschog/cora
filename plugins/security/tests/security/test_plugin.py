from cora.plugins.security import extend
from fakes import host_for


def test_it_registers_a_rule_and_nothing_else() -> None:
    """A guard, not a domain: the screen registers no persona and no tools, so loading
    it does not tell cora what it is for."""
    host = host_for("cora.plugins.security")

    extend(host)

    assert [entry.kind for entry in host.registered] == ["rule"]
