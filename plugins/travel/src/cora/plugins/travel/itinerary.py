"""The tool that saves an itinerary as a file the user keeps.

The one thing this plugin does that changes something outside cora, which is why it is
declared as having an effect and why a call of it waits for the user's word.
"""

import re
from typing import Any

from cora.ports.output import Output
from cora.ports.plugin import Tool, ToolRefusal

ITINERARY_TOOL_NAME = "save_itinerary"
ITINERARY_TOOL_DESCRIPTION = (
    "Save an itinerary you have worked out as a Markdown file the user keeps. Offer "
    "this when the plan is settled and they have said they want it; the user is asked "
    "to approve the save before it happens."
)
ITINERARY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": (
                "What the itinerary is called — it heads the file and names it."
            ),
        },
        "itinerary": {
            "type": "string",
            "description": "The itinerary itself, as Markdown.",
        },
    },
    "required": ["title", "itinerary"],
    "additionalProperties": False,
}
UNNAMEABLE = (
    "'{title}' leaves no filename behind once it is made safe to write; give the "
    "itinerary a title with some letters or digits in it"
)
"""What the model is told when a title reduces to nothing. The plugin's own refusal,
because the plugin is what turns a title into a name — cora refuses a name that escapes
the location, and this is the case that never reaches it."""
SUFFIX = ".md"
UNSAFE = re.compile(r"[^a-z0-9]+")


def itinerary_tool(output: Output) -> Tool:
    """The tool, bound to the one place this deployment lets an effect write.

    Handed the port rather than a path: where a file may go is the deployment's, and the
    check that a name stays there is cora's.
    """

    def save(title: str, itinerary: str) -> str:
        return _saved(output, title, itinerary)

    return Tool(
        name=ITINERARY_TOOL_NAME,
        description=ITINERARY_TOOL_DESCRIPTION,
        parameter_schema=ITINERARY_SCHEMA,
        run=save,
        effect=True,
    )


def _saved(output: Output, title: str, itinerary: str) -> str:
    """Write the itinerary under a name made out of its title, and say where it went.

    Raises:
        ToolRefusal: The title leaves no filename, or the name would not stay under the
            output location — which is cora's refusal, passed on as it was worded.
    """
    where = output.write(_filename(title), f"# {title}\n\n{itinerary.strip()}\n")
    return f"Saved the itinerary to {where}"


def _filename(title: str) -> str:
    """The title as a filename: lowercased, and everything else turned into a hyphen.

    Made rather than taken, because the title is the model's prose — a slash or a dot
    in it is a word to the model and a path to a filesystem.

    Raises:
        ToolRefusal: Nothing is left of the title once it is safe to write.
    """
    stem = UNSAFE.sub("-", title.lower()).strip("-")
    if not stem:
        raise ToolRefusal(UNNAMEABLE.format(title=title))
    return f"{stem}{SUFFIX}"
