from dataclasses import dataclass

from cora.domain.citations import CitableHits, Nothing
from cora.ports.context_source import ContextSource
from cora.ports.plugin import Tool

SEARCH_TOOL_NAME = "search_documents"
EMPTY_STORE = Nothing(
    told="No documents have been uploaded yet, so there was nothing to search.",
    shown="No documents uploaded yet.",
)
"""A fact, stated where the model can read it, and nothing more: the tool's result
arrives labelled untrusted data with instructions in it never to be followed, so what
to *do* about an empty store is a rule in the brief instead (`AGENT_RULES`).

Top-k comes back whatever the scores, so an empty result is an empty store rather than
a question the documents miss — pinned against real Chroma in the adapter's suite."""
SEARCH_TOOL_DESCRIPTION = (
    "Search the user's own documents and return the passages that match, each "
    "numbered so the answer can cite it. Call this whenever the answer should "
    "rest on what the documents say."
)


@dataclass(frozen=True)
class DocumentSearch:
    context_source: ContextSource
    top_k: int

    def __call__(self, query: str) -> CitableHits:
        return CitableHits(
            self.context_source.search(query, self.top_k), nothing=EMPTY_STORE
        )


def search_tool(context_source: ContextSource, top_k: int) -> Tool:
    return Tool(
        name=SEARCH_TOOL_NAME,
        description=SEARCH_TOOL_DESCRIPTION,
        parameter_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to look for, in the user's own words.",
                }
            },
            "required": ["query"],
        },
        run=DocumentSearch(context_source, top_k),
    )
