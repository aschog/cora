"""The plugin the browser suite runs against: one field, and one tool that acts.

Dropped in rather than installed, so the run covers the folder as well — and it gives
the suite the two things a bare cora has not got: a second field to pin a conversation
to, and a tool declaring it changes something outside cora, which is what the approval
gate stops on.
"""

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal

CONTRACT = 1
SCOPE = "kit"
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

    cora.register_tool(
        name="write_note",
        description="Write one note to a file.",
        parameter_schema=NOTE,
        run=write_note,
        effect=True,
        scope=SCOPE,
    )
