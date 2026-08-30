"""A plugin that registers all three kinds of contribution, for the outer test."""

from cora.domain.errors import InputRejectedError
from cora.ports.host import Host

INSTRUCTIONS = "You are the registering test plugin. Echo what the user asks you to."
REFUSAL = "The registering plugin will not answer shouting."
ECHO = "echo"


def echo(word: str) -> str:
    return word


class RefusesShouting:
    def apply(self, user_input: str) -> None:
        if user_input.isupper():
            raise InputRejectedError(REFUSAL)


def extend(cora: Host) -> None:
    cora.register_instructions(INSTRUCTIONS)
    cora.register_tool(
        name=ECHO,
        description="Echo one word back.",
        parameter_schema={
            "type": "object",
            "properties": {"word": {"type": "string"}},
            "required": ["word"],
        },
        run=echo,
    )
    cora.register_rule(RefusesShouting())
