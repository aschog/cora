from core.ports.plugin import Tool
from fixture_plugins import make_plugin, make_tool

PLUGIN = make_plugin(
    tools=(
        make_tool("one"),
        Tool(
            name="two",
            description="The two tool.",
            parameter_schema={"type": "object", "properties": {}},
            run="not callable",  # ty: ignore[invalid-argument-type]
        ),
    ),
)
