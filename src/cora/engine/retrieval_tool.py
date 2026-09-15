"""The tool that searches the user's own documents, and cites what it finds."""

from dataclasses import dataclass

from cora.domain.citations import CitableHits, Nothing
from cora.ports.context_source import ContextSource
from cora.ports.plugin import Tool

SEARCH_TOOL_NAME = "search_documents"
EMPTY_STORE = Nothing(
    told="No documents have been uploaded yet, so there was nothing to search.",
    shown="No documents uploaded yet.",
)
SEARCH_TOOL_DESCRIPTION = (
    "Search the user's own documents and return the passages that match, each "
    "numbered so the answer can cite it. Call this whenever the answer should "
    "rest on what the documents say."
)
UNCITED_SEARCH_DESCRIPTION = (
    "Search the user's own documents and return the passages that match, each headed "
    "by the document it came from. Call this whenever the answer should rest on what "
    "the documents say, and name the document rather than numbering it."
)


@dataclass(frozen=True)
class DocumentSearch:
    """What `search_documents` runs: one query against the documents behind it."""

    context_source: ContextSource
    top_k: int

    def __call__(self, query: str) -> CitableHits:
        """The passages found, as a payload that numbers itself to be cited."""
        return CitableHits(
            self.context_source.search(query, self.top_k), nothing=EMPTY_STORE
        )


def search_tool(
    context_source: ContextSource, top_k: int, *, cites: bool = True
) -> Tool:
    """The `search_documents` tool as the model is offered it.

    Args:
        cites: Whether this reader may hand out numbers. A reader that may not is told
            so by the description, because that is where it looks before calling.
    """
    return Tool(
        name=SEARCH_TOOL_NAME,
        description=SEARCH_TOOL_DESCRIPTION if cites else UNCITED_SEARCH_DESCRIPTION,
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
