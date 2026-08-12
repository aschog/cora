from cora.ports.plugin import Tool
from fixture_plugins import identity, make_plugin, make_tool

PLUGIN = make_plugin(
    tools=(
        make_tool("one"),
        Tool(
            name="two",
            description="The two tool.",
            parameter_schema={"type": "integr", "properties": []},
            run=identity,
        ),
    ),
)
