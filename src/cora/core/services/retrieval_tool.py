from dataclasses import dataclass

from cora.core.citations import CitableHits
from cora.core.context_source import ContextSource
from cora.core.ports.plugin import Tool

SEARCH_TOOL_NAME = "search_documents"
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
        return CitableHits(self.context_source.search(query, self.top_k))


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
