from cora.ports.host import SCREENING, Extension, Handler, Host
from cora.ports.plugin import Tool

REFUSAL = "The test plugin refused that."


def refuses_containing(trigger: str, message: str = REFUSAL) -> Handler:
    """A plugin's screen, in the shape every real one has: it reads the question, and it
    refuses or it does not. Written here so a suite can prove the engine runs a plugin's
    screen without installing a plugin to borrow one from."""

    def screen(question: str) -> str | None:
        return message if trigger.lower() in question.lower() else None

    return screen


def identity(x: int) -> int:
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
        run=identity,
    )


def make_plugin(
    name: str = "valid",
    instructions: str = "You are a test plugin.",
    tools: tuple[Tool, ...] | None = None,
    screens: tuple[Handler, ...] = (),
    scope: str | None = None,
) -> Extension:
    """One plugin as a test wants it: `tools=None` asks for the three default tools,
    and `tools=()` for none. `name` is the module's last segment, which is what heads
    its section of the brief and what its settings are named for. `scope` is where
    everything it registers applies, and `None` is everywhere."""
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
