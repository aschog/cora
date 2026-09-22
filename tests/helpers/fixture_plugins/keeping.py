from cora.ports.host import Host

KEEP_TOOL = "keep_note"
READ_TOOL = "read_note"
NOTE = "note"
NOTHING = "nothing was kept"
AT_LOAD = "written while loading"


def extend(cora: Host) -> None:
    # Dropped: there is no conversation to keep it for while a plugin is loading.
    cora.state.keep(NOTE, AT_LOAD)

    def keep(text: str) -> str:
        cora.state.keep(NOTE, text)
        return f"kept {text}"

    def read() -> str:
        return cora.state.read(NOTE) or NOTHING

    cora.register_tool(
        name=KEEP_TOOL,
        description="Keep a note for the rest of this conversation.",
        parameter_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        run=keep,
    )
    cora.register_tool(
        name=READ_TOOL,
        description="Read the note kept earlier in this conversation.",
        parameter_schema={"type": "object", "properties": {}},
        run=read,
    )
