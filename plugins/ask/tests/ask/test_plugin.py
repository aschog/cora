from cora.plugins.ask import extend
from cora.ports.host import INSTRUCTIONS, TOOL
from fakes import host_for


def test_it_registers_the_fork_the_form_and_a_section_system_wide() -> None:
    host = host_for("cora.plugins.ask")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (TOOL, None),
        (TOOL, None),
        (INSTRUCTIONS, None),
    ]
    fork, form = (entry.value for entry in host.registered if entry.kind == TOOL)
    assert (fork.name, form.name) == ("ask_user", "ask_user_for")
    assert fork.asks is not None and form.asks is not None
    assert not fork.effect and not form.effect
