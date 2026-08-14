from cora.plugins.security.injection import PromptInjectionRule
from cora.ports.plugin import Plugin

PLUGIN = Plugin(
    name="Prompt safety",
    validation_rules=(PromptInjectionRule(),),
)
"""Rules alone: the screen contributes no persona, no tools and no scope, so cora
carries a guard without carrying a domain. It ships in the default set, which is what
makes the box safe without making it opinionated — and `CORA_PLUGINS=` opts out."""
