from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal

CONTRACT = 1
SCOPE = "kit"
INSTRUCTIONS = "You are a note-keeper. Keep what the user worked out, when asked."
NOTE = {
    "type": "object",
    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
    "required": ["title", "body"],
}


def extend(cora: Host) -> None:
    output = cora.output

    def write_note(title: str, body: str) -> str:
        if output is None:
            raise ToolRefusal("this deployment keeps nothing")
        return f"written to {output.write(f'{title}.md', body)}"

    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    cora.register_tool(
        name="write_note",
        description="Write one note to a file.",
        parameter_schema=NOTE,
        run=write_note,
        effect=True,
        scope=SCOPE,
    )
