import pathlib

from cora.plugins.travel.forecast import (
    FORECAST_SCHEMA,
    FORECAST_TOOL_DESCRIPTION,
    FORECAST_TOOL_NAME,
    Forecast,
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
- Ask for the dates when the answer turns on them, rather than assuming a season.
- Never invent a price, a timetable or an address.
"""

CORPUS = pathlib.Path(__file__).parent / "corpus"
"""The notes this plugin ships, as files the user uploads like any other document.

A directory rather than a registration: cora ingests what is uploaded, and a plugin that
seeded the index at load would re-embed its corpus on every start. Story 8 gives a scope
its own document directory, and that is where this stops being a folder to upload from.
"""


def extend(cora: Host) -> None:
    """Instructions and one tool, both under the travel scope and neither outside it.

    The forecast is declared as returning material cora did not write, which is what
    puts a service's answer behind the same label a passage of the user's own documents
    carries. Nothing here is system-wide: a turn about training is offered no weather.
    """
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    cora.register_tool(
        name=FORECAST_TOOL_NAME,
        description=FORECAST_TOOL_DESCRIPTION,
        parameter_schema=FORECAST_SCHEMA,
        run=Forecast(),
        scope=SCOPE,
        untrusted=True,
    )
