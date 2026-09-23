from cora.ports.host import BRIEFING, Host

from .brief import remembered
from .remember import (
    MAX_FACT_CHARS,
    REMEMBER_DESCRIPTION,
    REMEMBER_TOOL_NAME,
    RememberFact,
)

RULE = (
    f"Call the {REMEMBER_TOOL_NAME} tool only when the user asks you to remember "
    'something — "remember that…", "keep this in mind…". Never decide for '
    "yourself that something is worth keeping."
)
NO_MEMORY = "this deployment keeps no memory, so nothing is registered"


def extend(cora: Host) -> None:
    """What cora remembers about the user, as behaviour over the store it is handed.

    One tool that keeps a fact when asked, one rule saying only then, and a handler
    that writes the notes into every brief — with the subjects held at more than one
    value named, so the model settles them with the ask plugin's fork instead of
    picking. A deployment keeping no memory gets none of it, and its log says why."""
    memory = cora.memory
    if memory is None:
        cora.log.info(NO_MEMORY)
        return
    cora.register_tool(
        name=REMEMBER_TOOL_NAME,
        description=REMEMBER_DESCRIPTION,
        parameter_schema={
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "maxLength": MAX_FACT_CHARS,
                    "description": (
                        "The fact, in the third person and standing on its own — "
                        "'trains on Tuesdays', not 'I train then'."
                    ),
                }
            },
            "required": ["fact"],
        },
        run=RememberFact(memory),
        writes=True,
    )
    cora.register_instructions(RULE)
    cora.register_handler(
        event=BRIEFING, handle=lambda brief: remembered(brief, memory.recall())
    )
