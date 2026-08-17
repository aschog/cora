from cora.domain.errors import InputRejectedError
from cora.ports.plugin import Plugin, Tool, ValidationRule

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
    name: str = "test",
    instructions: str = "You are a test plugin.",
    tools: tuple[Tool, ...] | None = None,
    validation_rules: tuple[ValidationRule, ...] = (),
) -> Plugin:
    """`tools=None` asks for the three default tools; `tools=()` for none."""
    if tools is None:
        tools = (make_tool("one"), make_tool("two"), make_tool("three"))
    return Plugin(
        name=name,
        instructions=instructions,
        tools=tools,
        validation_rules=validation_rules,
    )
