from cora.ports.host import SCREENING, Extension, Handler, Host
from cora.ports.plugin import Tool

REFUSAL = "The test plugin refused that."


def refuses_containing(trigger: str, message: str = REFUSAL) -> Handler:

    def screen(question: str) -> str | None:
        return message if trigger.lower() in question.lower() else None

    return screen


def identity(x: int) -> int:
    return x


def make_tool(name: str, *, effect: bool = False) -> Tool:
    return Tool(
        name=name,
        description=f"The {name} tool.",
        parameter_schema={
            "type": "object",
            "properties": {"x": {"type": "integer"}},
            "required": ["x"],
        },
        run=identity,
        effect=effect,
    )


def make_plugin(
    name: str = "valid",
    instructions: str = "You are a test plugin.",
    tools: tuple[Tool, ...] | None = None,
    screens: tuple[Handler, ...] = (),
    scope: str | None = None,
) -> Extension:
    offered = (
        (make_tool("one"), make_tool("two"), make_tool("three"))
        if tools is None
        else tools
    )

    def extend(cora: Host) -> None:
        if instructions.strip():
            cora.register_instructions(instructions, scope=scope)
        for tool in offered:
            cora.register_tool(
                name=tool.name,
                description=tool.description,
                parameter_schema=tool.parameter_schema,
                run=tool.run,
                scope=scope,
            )
        for screen in screens:
            cora.register_handler(event=SCREENING, handle=screen, scope=scope)

    return Extension(module=f"fixture_plugins.{name}", extend=extend)
