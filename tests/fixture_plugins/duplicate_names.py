from docchat.plugin import Plugin
from fixture_plugins import make_tool

PLUGIN = Plugin(
    system_prompt="You are a test plugin.",
    tools=(make_tool("one"), make_tool("one"), make_tool("two")),
    validation_rules=(),
)
