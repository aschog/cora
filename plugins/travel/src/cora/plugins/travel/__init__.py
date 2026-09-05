import pathlib

from cora.domain.errors import PluginLoadError
from cora.plugins.travel.forecast import forecast_tool
from cora.plugins.travel.itinerary import itinerary_tool
from cora.plugins.travel.researcher import (
    RESEARCH_SCHEMA,
    RESEARCH_TOOL_DESCRIPTION,
    RESEARCH_TOOL_NAME,
    researching,
)
from cora.plugins.travel.trips import ENDPOINT, SEARCH, SETTING, trip_tools
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
- Search live prices when the answer turns on cost. Give the flight search a window —
  an earliest start, a latest return and a number of nights — whenever the traveller
  has not fixed the dates, and let it try the departures across it. Carry their budget
  and any restriction into the search rather than filtering afterwards, and say the
  prices are what the aggregator showed rather than a seat held for them.
- Offer to save the itinerary once a plan is settled and the user wants it — the save
  is put to them for approval before it happens, so offer rather than announce, and say
  where the file went once it is done.
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
    """Instructions and up to five tools, all under travel and none outside it.

    Four are declared as returning material cora did not write: a service's answer is
    not cora's words, and neither is a report the researcher built out of documents and
    a forecast. The last changes something outside cora and says so, so a call of it
    waits for the user. Nothing here is system-wide, so a turn about training is offered
    no weather, no researcher and no prices.

    Two of them are offered only where the deployment set a key for the search service,
    and saving only where it configured somewhere to write. A tool the model can call
    and that can only fail is worse than one it is never offered — the same reason cora
    offers no `remember` without a memory.

    Raises:
        PluginLoadError: The rounds setting is not a whole number. Raised as one of
            these rather than left as the `ValueError` underneath, because cora keeps a
            plugin's exception text out of what the operator reads — it could be
            carrying a key. A refusal a plugin raises itself reaches them as worded, so
            this is the channel for saying which setting to go and fix.
    """
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
    # One tool, registered for the turn and handed to the researcher's loop: it holds
    # an HTTP client, and a second would parse the certificate bundle over again.
    fetching = forecast_tool()
    cora.register_tool(
        name=fetching.name,
        description=fetching.description,
        parameter_schema=fetching.parameter_schema,
        run=fetching.run,
        scope=SCOPE,
        untrusted=fetching.untrusted,
        effect=fetching.effect,
    )
    try:
        research = researching(cora, fetching)
    except ValueError as unreadable:
        raise PluginLoadError(__name__, str(unreadable)) from unreadable
    cora.register_tool(
        name=RESEARCH_TOOL_NAME,
        description=RESEARCH_TOOL_DESCRIPTION,
        parameter_schema=RESEARCH_SCHEMA,
        run=research,
        scope=SCOPE,
        untrusted=True,
    )
    key = cora.settings.get(SETTING, "").strip()
    endpoint = cora.settings.get(ENDPOINT, "").strip() or SEARCH
    for priced in trip_tools(key, endpoint) if key else ():
        cora.register_tool(
            name=priced.name,
            description=priced.description,
            parameter_schema=priced.parameter_schema,
            run=priced.run,
            scope=SCOPE,
            untrusted=priced.untrusted,
            asks=priced.asks,
        )
    if cora.output is None:
        return
    saving = itinerary_tool(cora.output)
    cora.register_tool(
        name=saving.name,
        description=saving.description,
        parameter_schema=saving.parameter_schema,
        run=saving.run,
        scope=SCOPE,
        effect=saving.effect,
    )
