from cora.plugins.security import extend
from cora.ports.host import HANDLER, SCREENING
from fakes import host_for


def test_it_subscribes_a_system_wide_screen_and_nothing_else() -> None:
    """A guard, not a domain: it registers no persona and no tools, so loading it does
    not tell cora what it is for. And under no scope, so nothing can switch it off."""
    host = host_for("cora.plugins.security")

    extend(host)

    [entry] = host.registered
    assert (entry.kind, entry.scope) == (HANDLER, None)
    assert entry.value.event == SCREENING
