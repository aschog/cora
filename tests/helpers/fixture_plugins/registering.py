"""A plugin that registers all three kinds of contribution, for the outer test."""

from cora.ports.host import SCREENING, Host

INSTRUCTIONS = "You are the registering test plugin. Echo what the user asks you to."
REFUSAL = "The registering plugin will not answer shouting."
ECHO = "echo"


def echo(word: str) -> str:
    return word


def refuse_shouting(question: str) -> str | None:
    return REFUSAL if question.isupper() else None


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
    cora.register_handler(event=SCREENING, handle=refuse_shouting)
