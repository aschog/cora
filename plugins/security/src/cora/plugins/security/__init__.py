from cora.ports.host import SCREENING, Host

from .injection import refuse_injection


def extend(cora: Host) -> None:
    """A screen and nothing else: it contributes no persona and no tools, so a
    deployment can name it beside a domain plugin and carry a guard without carrying a
    second domain. System-wide, and so under no scope: an injection attempt is refused
    whatever the turn was running as. Like every plugin it is named in `CORA_PLUGINS`
    or it is not there — cora starts with none, and says so."""
    cora.register_handler(event=SCREENING, handle=refuse_injection)
