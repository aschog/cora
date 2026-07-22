from docchat.plugin import Plugin
from fixture_plugins import make_tool

PLUGIN = Plugin(
    system_prompt="   ",
    tools=(make_tool("one"), make_tool("two"), make_tool("three")),
    validation_rules=(),
)
