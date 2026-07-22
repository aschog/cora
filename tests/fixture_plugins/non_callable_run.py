from docchat.plugin import Plugin, Tool
from fixture_plugins import make_tool

PLUGIN = Plugin(
    system_prompt="You are a test plugin.",
    tools=(
        make_tool("one"),
        Tool(
            name="two",
            description="The two tool.",
            parameter_schema={"type": "object", "properties": {}},
            run="not callable",  # ty: ignore[invalid-argument-type]
        ),
    ),
    validation_rules=(),
)
