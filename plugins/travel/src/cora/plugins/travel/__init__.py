import pathlib

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
    """Instructions under the travel scope, and nothing else — yet."""
    cora.register_instructions(INSTRUCTIONS, scope=SCOPE)
