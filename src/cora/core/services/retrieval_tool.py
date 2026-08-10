from cora.core.citations import CitableHits
from cora.core.context_source import ContextSource
from cora.core.ports.plugin import Tool

SEARCH_TOOL_NAME = "search_documents"
SEARCH_TOOL_DESCRIPTION = (
    "Search the user's own documents and return the passages that match, each "
    "numbered so the answer can cite it. Call this whenever the answer should "
    "rest on what the documents say."
)
SEARCH_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "What to look for, in the user's own words.",
        }
    },
    "required": ["query"],
}


def search_tool(context_source: ContextSource, top_k: int) -> Tool:
    def run(query: str) -> CitableHits:
        return CitableHits(context_source.search(query, top_k))

    return Tool(
        name=SEARCH_TOOL_NAME,
        description=SEARCH_TOOL_DESCRIPTION,
        parameter_schema=SEARCH_TOOL_SCHEMA,
        run=run,
    )
