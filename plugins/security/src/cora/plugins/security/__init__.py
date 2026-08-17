from cora.plugins.security.injection import PromptInjectionRule
from cora.ports.plugin import Plugin

PLUGIN = Plugin(
    name="Prompt safety",
    validation_rules=(PromptInjectionRule(),),
)
"""Rules alone: the screen contributes no persona and no tools, so a deployment can name
it beside a domain plugin and carry a guard without carrying a second domain. Like every
plugin it is named in `CORA_PLUGINS` or it is not there — cora starts with none, and
says so."""
