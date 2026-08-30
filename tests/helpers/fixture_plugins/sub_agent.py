"""A plugin whose tool runs a turn of its own, through the host it was handed.

The acid test for the contract: a sub-agent is a plugin someone wrote, and cora needed
no change to allow one.
"""

from cora.ports.host import Host

RESEARCH = "research"
ROUNDS = 2


def extend(cora: Host) -> None:
    def research(question: str) -> str:
        return cora.delegate(question, rounds=ROUNDS)

    cora.register_tool(
        name=RESEARCH,
        description="Look a question up and answer it in a sentence.",
        parameter_schema={
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
        run=research,
    )
