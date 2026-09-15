"""The tool that digs, over several lookups, and comes back with one report.

A plugin, not a feature: it is a tool whose `run` asks the host for a loop of its own,
hands it the forecast beside cora's document search, and answers with what the loop
wrote. Nothing in cora was changed to allow it — which is the claim the plugin contract
makes, and this is where a reader watches it hold.
"""

from collections.abc import Callable, Mapping

from cora.ports.host import Host
from cora.ports.plugin import Tool

RESEARCH_TOOL_NAME = "research_trip"
RESEARCH_TOOL_DESCRIPTION = (
    "Research a trip question that needs several lookups — what to see over three "
    "days, what is open when, what the weather will do — and come back with one "
    "report. Call this instead of searching several times yourself: the digging "
    "happens out of the way, and you are handed what it found."
)
RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string",
            "description": "What to research, in a sentence.",
        }
    },
    "required": ["question"],
}

ROUNDS = "rounds"
DEFAULT_ROUNDS = 3

TASK = (
    "Research this for someone planning a trip: {question}\n\n"
    "Look things up one at a time, using the documents and the forecast. Then report "
    "what you found in a few sentences, naming where each fact came from. Say plainly "
    "what you could not find rather than filling the gap."
)


def rounds_from(settings: Mapping[str, str]) -> int:
    """How many rounds this deployment allows the researcher.

    Args:
        settings: This plugin's own slice of the environment, as the host hands it over.

    Raises:
        ValueError: The setting is not a whole number above zero. Raised while the
            plugin registers, so the deployment is refused at load with this plugin
            named, rather than a typo quietly becoming the default.
    """
    named = settings.get(ROUNDS)
    if named is None:
        return DEFAULT_ROUNDS
    try:
        rounds = int(named)
    except ValueError as unreadable:
        raise ValueError(
            f"{ROUNDS} must be a whole number, but got {named!r}"
        ) from unreadable
    if rounds < 1:
        raise ValueError(f"{ROUNDS} must be 1 or more, but got {rounds}")
    return rounds


def researching(cora: Host, *lookups: Tool) -> Callable[[str], str]:
    """What `research_trip` runs, closed over the host and the tools it may pass on.

    Closed over rather than handed them per call, because by the time the model calls
    this there is no host in scope — the same reason cora's own tools are built at
    assembly. The tools are taken here rather than built here for the same reason: one
    of them holds an HTTP client, and building a client per question would parse the
    certificate bundle again and reuse no connection from the question before.

    Raises:
        ValueError: The rounds setting is not a whole number.
    """
    rounds = rounds_from(cora.settings)

    def research(question: str) -> str:
        return cora.delegate(
            TASK.format(question=question), tools=lookups, rounds=rounds
        )

    return research
