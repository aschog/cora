from cora.plugins.security.injection import PromptInjectionRule
from cora.ports.host import Host


def extend(cora: Host) -> None:
    """A rule and nothing else: the screen contributes no persona and no tools, so a
    deployment can name it beside a domain plugin and carry a guard without carrying a
    second domain. Like every plugin it is named in `CORA_PLUGINS` or it is not there —
    cora starts with none, and says so."""
    cora.register_rule(PromptInjectionRule())
