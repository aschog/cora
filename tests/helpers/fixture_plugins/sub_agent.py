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
