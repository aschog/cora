import json
from dataclasses import dataclass

from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ChatModel, Message
from cora.core.query_plan import QueryPlan


@dataclass(frozen=True)
class QueryPlanner:
    chat_model: ChatModel
    num_queries: int

    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan:
        messages = _planning_messages(question, sources, self.num_queries)
        reply = self.chat_model.complete(messages, ())
        return parse_plan(reply.text, sources)


def parse_plan(text: str, sources: tuple[str, ...]) -> QueryPlan:
    data = json.loads(text)
    source = data.get("source")
    metadata_filter = (
        MetadataFilter(field="source", value=source)
        if isinstance(source, str) and source in sources
        else None
    )
    return QueryPlan(queries=tuple(data["queries"]), metadata_filter=metadata_filter)


def _planning_messages(
    question: str, sources: tuple[str, ...], num_queries: int
) -> tuple[Message, ...]:
    catalogue = ", ".join(sources) if sources else "(none)"
    instruction = (
        f"Rewrite the question into {num_queries} search queries that surface "
        "relevant passages. Optionally restrict the search to one document by its "
        f"exact name from this list: {catalogue}. Reply with JSON only: "
        '{"queries": [string, ...], "source": string or null}.'
    )
    return (
        Message(role="system", content=instruction),
        Message(role="user", content=question),
    )
