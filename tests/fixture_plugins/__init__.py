from docchat.plugin import Plugin, Tool


def _identity(x: int) -> int:
    return x


def make_tool(name: str) -> Tool:
    return Tool(
        name=name,
        description=f"The {name} tool.",
        parameter_schema={
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        },
        run=_identity,
    )


def make_plugin(
    system_prompt: str = "You are a test plugin.",
    tools: tuple[Tool, ...] | None = None,
) -> Plugin:
    if tools is None:
        tools = (make_tool("one"), make_tool("two"), make_tool("three"))
    return Plugin(system_prompt=system_prompt, tools=tools, validation_rules=())
