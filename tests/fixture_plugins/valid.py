from docchat.plugin import Plugin, Tool


def _identity(x: int) -> int:
    return x


def _tool(name: str) -> Tool:
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


PLUGIN = Plugin(
    system_prompt="You are a test plugin.",
    tools=(_tool("one"), _tool("two"), _tool("three")),
    validation_rules=(),
)
