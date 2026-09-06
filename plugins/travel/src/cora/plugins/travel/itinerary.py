"""The tool that saves an itinerary as a file the user keeps.

The one thing this plugin does that changes something outside cora, which is why it is
declared as having an effect and why a call of it waits for the user's word.
"""

import hashlib
import json
import re
from typing import Any

from cora.plugins.travel.plan import Plan, plan_from
from cora.plugins.travel.planner import KEPT as PLAN_KEPT
from cora.ports.host import Host
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
        "depart": {"type": "string", "format": "date"},
        "back": {"type": "string", "format": "date"},
        "flight": {"type": "string", "description": "The fare, as it was priced."},
        "stay": {"type": "string", "description": "The stay, as it was priced."},
        "total": {"type": "string", "description": "What the trip comes to."},
        "days": {
            "type": "array",
            "items": {"type": "string"},
            "description": "One line per day, as the plan has them.",
        },
    },
    "required": ["title", "depart", "back", "flight", "stay", "total", "days"],
    "additionalProperties": False,
}
"""Flat rather than one nested plan, because the card put to the traveller lays out one
read-only field per top-level argument: a plan inside one field is a plan nobody read
before approving it."""

NOTHING_PLANNED = (
    "No trip has been planned in this conversation, so there is nothing verified to "
    "save. Plan one first."
)
NOT_THE_PLAN = (
    "That is not the trip I checked, so I have not saved it. Ask me to plan or revise "
    "the trip, and save what comes back."
)
UNNAMEABLE = (
    "'{title}' leaves no filename behind once it is made safe to write; give the "
    "itinerary a title with some letters or digits in it"
)
"""What the model is told when a title reduces to nothing. The plugin's own refusal,
because the plugin is what turns a title into a name — cora refuses a name that escapes
the location, and this is the case that never reaches it."""
UNPRICED = "unpriced"
SUFFIX = ".md"
UNSAFE = re.compile(r"[^a-z0-9]+")
HASH_LENGTH = 12
"""How much of the itinerary's hash goes in its filename, as `FileDocuments` puts the
head of an upload's hash in its own. It is what makes one title saved twice two files
rather than one overwritten — a revised plan is not a correction of the plan the user
already approved, and this is a file they keep."""


def flat(plan: Plan) -> dict[str, Any]:
    """The plan as the save takes it, which is also how the card shows it.

    Written once and read twice — the arguments a call carries and the arguments the
    kept plan is compared against — so the comparison cannot drift from the card.
    """
    return {
        "depart": plan.depart.isoformat(),
        "back": plan.back.isoformat(),
        "flight": plan.fare.line if plan.fare else UNPRICED,
        "stay": plan.stay.line if plan.stay else UNPRICED,
        "total": (
            f"{plan.currency} {plan.total:g}" if plan.total is not None else UNPRICED
        ),
        "days": [
            f"{day.on}: {', '.join(day.doing) or 'nothing planned'}"
            for day in plan.days
        ],
    }


def itinerary_tool(output: Output, cora: Host) -> Tool:
    """The tool, bound to the one place this deployment lets an effect write.

    Handed the port rather than a path: where a file may go is the deployment's, and the
    check that a name stays there is cora's. Handed the host too, because what may be
    written is the plan this conversation actually verified and nothing else.
    """

    def save(title: str, **given: Any) -> str:
        return _saved(output, cora, title, given)

    return Tool(
        name=ITINERARY_TOOL_NAME,
        description=ITINERARY_TOOL_DESCRIPTION,
        parameter_schema=ITINERARY_SCHEMA,
        run=save,
        effect=True,
    )


def _saved(output: Output, cora: Host, title: str, given: dict[str, Any]) -> str:
    """Write the plan this conversation verified, and say where it went.

    What arrived is compared against what was kept rather than trusted: the gate shows
    the traveller these arguments, and a model free to rewrite them between the check
    and the write would have them approve one plan and save another.

    Raises:
        ToolRefusal: Nothing has been planned here, what arrived is not the plan that
            was checked, the title leaves no filename, or the name would not stay under
            the output location.
    """
    held = cora.state.read(PLAN_KEPT)
    if held is None:
        raise ToolRefusal(NOTHING_PLANNED)
    verified = flat(plan_from(json.loads(held)))
    arrived = {name: given.get(name) for name in verified}
    if arrived != verified:
        raise ToolRefusal(NOT_THE_PLAN)
    kept = f"# {title}\n\n{_written(verified).strip()}\n"
    where = output.write(_filename(title, kept), kept)
    return f"Saved the itinerary to {where}"


def _written(plan: dict[str, Any]) -> str:
    """The verified plan as the Markdown that lands in the file."""
    lines = [
        f"**{plan['depart']} to {plan['back']}**",
        "",
        f"- Flight: {plan['flight']}",
        f"- Stay: {plan['stay']}",
        f"- Total: {plan['total']}",
        "",
    ]
    lines.extend(f"- {day}" for day in plan["days"])
    return "\n".join(lines)


def _filename(title: str, kept: str) -> str:
    """The title as a filename, with the head of what was saved hashed onto the end.

    Made rather than taken, because the title is the model's prose — a slash or a dot
    in it is a word to the model and a path to a filesystem. The hash is of the text
    rather than of the moment, so the same plan saved twice is one file and a revised
    one is a second: nothing the user approved is written over.

    Raises:
        ToolRefusal: Nothing is left of the title once it is safe to write.
    """
    stem = UNSAFE.sub("-", title.lower()).strip("-")
    if not stem:
        raise ToolRefusal(UNNAMEABLE.format(title=title))
    marked = hashlib.sha256(kept.encode()).hexdigest()[:HASH_LENGTH]
    return f"{stem}-{marked}{SUFFIX}"
