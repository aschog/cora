import hashlib
from dataclasses import dataclass

from cora.ports.host import UPLOADING, Host

from .ingestion import Refused, ingest, reads
from .loaders import LOADERS
from .search import SEARCH_DESCRIPTION, SEARCH_SCHEMA, SEARCH_TOOL_NAME, DocumentSearch

DEFAULT_TOP_K = 5
RULE = (
    f"Call the {SEARCH_TOOL_NAME} tool whenever the answer should rest on the "
    "user's own documents, and cite the numbered passages it returns as [n]. "
    "Answer directly when the question needs no documents. "
    "If a search comes back with no passages at all, the user has uploaded nothing: "
    "say so, ask them to upload the documents that would cover it, and never fill "
    "the gap from your own knowledge. An empty search ends only the reading — "
    "whatever your other tools can still do for the question, go on and do it."
)
NOT_THERE = "Could not process '{name}': the upload was not there to read."


def extend(cora: Host) -> None:
    """The user's documents as behaviour: what indexes an upload, and what searches.

    An upload the reader makes is heard, read by its kind, cleaned, cut and put into
    the field's index; one of a kind this plugin cannot read is left as the file it
    landed as. The search tool numbers what it finds so the answer can cite it, and
    the brief says when to call it. How deep a search goes is this plugin's setting."""
    cora.register_tool(
        name=SEARCH_TOOL_NAME,
        description=SEARCH_DESCRIPTION,
        parameter_schema=SEARCH_SCHEMA,
        run=DocumentSearch(cora.documents, _top_k(cora.settings.get("top_k"))),
    )
    cora.register_instructions(RULE)
    cora.register_handler(event=UPLOADING, handle=Indexer(cora).landed)


@dataclass(frozen=True)
class Indexer:
    cora: Host

    def landed(self, name: str) -> str | None:
        # A kind this plugin does not read is left where it landed: the file is the
        # field's, and a plugin that cannot index it has nothing to say about whether
        # the field may hold it. What it reads and cannot — empty, corrupt, too large —
        # it does refuse, because there the reader asked for a document and has none.
        if not reads(name, LOADERS):
            return None
        data = self.cora.files.read_bytes(name)
        if data is None:
            return NOT_THERE.format(name=name)
        try:
            text, chunks = ingest(data, name, LOADERS)
        except Refused as refused:
            return refused.said
        upload = hashlib.sha256(data).hexdigest()
        self.cora.index.add(upload, name, text, chunks)
        return None


def _top_k(setting: str | None) -> int:
    return (
        int(setting)
        if setting and setting.isdigit() and int(setting) > 0
        else DEFAULT_TOP_K
    )
