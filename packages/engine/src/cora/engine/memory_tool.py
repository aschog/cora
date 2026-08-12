from dataclasses import dataclass

from cora.ports.memory import Memory
from cora.ports.plugin import Tool

REMEMBER_TOOL_NAME = "remember"
REMEMBER_TOOL_DESCRIPTION = (
    "Keep one durable fact about the user — a goal, a constraint, a preference, "
    "anything that should still be true next session. Call this when the user "
    "shares something about themselves, never for what a document says."
)


@dataclass(frozen=True)
class RememberFact:
    memory: Memory

    def __call__(self, fact: str) -> str:
        self.memory.remember(fact)
        return f"Remembered: {fact}"


def remember_tool(memory: Memory) -> Tool:
    return Tool(
        name=REMEMBER_TOOL_NAME,
        description=REMEMBER_TOOL_DESCRIPTION,
        parameter_schema={
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": (
                        "The fact, in the third person and standing on its own — "
                        "'trains on Tuesdays', not 'I train then'."
                    ),
                }
            },
            "required": ["fact"],
        },
        run=RememberFact(memory),
    )
