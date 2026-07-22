from docchat.plugin import Plugin, Tool
from fixture_plugins import _identity, make_tool

PLUGIN = Plugin(
    system_prompt="You are a test plugin.",
    tools=(
        make_tool("one"),
        Tool(
            name="two",
            description="The two tool.",
            parameter_schema={"type": "integr", "properties": []},
            run=_identity,
        ),
    ),
    validation_rules=(),
)
