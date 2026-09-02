import pathlib

from cora.plugins.travel.forecast import forecast_tool
from cora.plugins.travel.researcher import (
    RESEARCH_SCHEMA,
    RESEARCH_TOOL_DESCRIPTION,
    RESEARCH_TOOL_NAME,
    researching,
)
from cora.ports.host import Host

SCOPE = "travel"
"""What this plugin's field is called. Everything it registers is under it: a travel
persona has no business in a turn about training, and cora is not both at once."""

INSTRUCTIONS = """\
Answer travel questions — destinations, routes, timing, packing and logistics — from the
user's own documents.

- Search the documents for anything about a place, a route or a booking, then cite the
  numbered passages you used.
- Say plainly when what you have is out of date: an opening time or a fare in a document
  is what that document said, not what is true today.
- Fetch the forecast when the answer turns on the weather, and report it in your own
  words — it comes from a live service, so there is no passage to cite for it. Say
  where it came from, and say so too when the service could not be reached.
- Send the researcher when a question needs several lookups — three days somewhere,
  what is open, what the weather will do — rather than searching over and over
  yourself. Answer from the report it brings back, and if the report says it stopped
  early, say which part is still unresearched.
- Ask for the dates when the answer turns on them, rather than assuming a season.
- Never invent a price, a timetable or an address.
"""

CORPUS = pathlib.Path(__file__).parent / "corpus"
"""The notes this plugin ships, as files the user uploads like any other document.

A directory rather than a registration: cora ingests what is uploaded, and a plugin that
seeded the index at load would re-embed its corpus on every start. A field owning its
own document directory did not change that: what is uploaded is still the reader's to
choose, and these are files they may choose.
"""


def extend(cora: Host) -> None:
    """Instructions and two tools, all under the travel scope and none outside it.

    Both tools are declared as returning material cora did not write: a service's
    answer is not cora's words, and neither is a report the researcher built out of
    documents and a forecast. Nothing here is system-wide, so a turn about training is
    offered no weather and no researcher.

    Raises:
        ValueError: The rounds setting is not a whole number. Raised here so the
            deployment is refused at load with this plugin named.
    """
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    fetching = forecast_tool()
    cora.register_tool(
        name=fetching.name,
        description=fetching.description,
        parameter_schema=fetching.parameter_schema,
        run=fetching.run,
        scope=SCOPE,
        untrusted=fetching.untrusted,
    )
    cora.register_tool(
        name=RESEARCH_TOOL_NAME,
        description=RESEARCH_TOOL_DESCRIPTION,
        parameter_schema=RESEARCH_SCHEMA,
        run=researching(cora),
        scope=SCOPE,
        untrusted=True,
    )
