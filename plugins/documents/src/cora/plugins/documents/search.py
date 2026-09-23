from dataclasses import dataclass
from typing import Any

from cora.domain.citations import CitableHits, Nothing
from cora.ports.context_source import ContextSource

SEARCH_TOOL_NAME = "search_documents"
EMPTY_STORE = Nothing(
    told="No documents have been uploaded yet, so there was nothing to search.",
    shown="No documents uploaded yet.",
)
SEARCH_DESCRIPTION = (
    "Search the user's own documents and return the passages that match, each "
    "numbered so the answer can cite it. Call this whenever the answer should "
    "rest on what the documents say."
)
SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "What to look for, in the user's own words.",
        }
    },
    "required": ["query"],
}


@dataclass(frozen=True)
class DocumentSearch:
    """What `search_documents` runs: one query against the field's documents."""

    documents: ContextSource
    top_k: int

    def __call__(self, query: str) -> CitableHits:
        return CitableHits(
            self.documents.search(query, self.top_k), nothing=EMPTY_STORE
        )
