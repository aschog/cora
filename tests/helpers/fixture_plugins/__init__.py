from cora.domain.errors import InputRejectedError
from cora.ports.host import Extension, Host
from cora.ports.plugin import Tool, ValidationRule

REFUSAL = "The test plugin refused that."


class RefusesContaining:
    """A plugin's screen, in the shape every real one has: it reads the question, it
    refuses or it does not. Written here so a suite can prove the engine runs a plugin's
    rules without installing a plugin to borrow a rule from."""

    def __init__(self, trigger: str, message: str = REFUSAL) -> None:
        self.trigger = trigger
        self.message = message

    def apply(self, user_input: str) -> None:
        if self.trigger.lower() in user_input.lower():
            raise InputRejectedError(self.message)


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
    validation_rules: tuple[ValidationRule, ...] = (),
) -> Extension:
    """One plugin as a test wants it: `tools=None` asks for the three default tools,
    and `tools=()` for none. `name` is the module's last segment, which is what heads
    its section of the brief and what its settings are named for."""
    offered = (
        (make_tool("one"), make_tool("two"), make_tool("three"))
        if tools is None
        else tools
    )

    def extend(cora: Host) -> None:
        if instructions.strip():
            cora.register_instructions(instructions)
        for tool in offered:
            cora.register_tool(
                name=tool.name,
                description=tool.description,
                parameter_schema=tool.parameter_schema,
                run=tool.run,
            )
        for rule in validation_rules:
            cora.register_rule(rule)

    return Extension(module=f"fixture_plugins.{name}", extend=extend)
