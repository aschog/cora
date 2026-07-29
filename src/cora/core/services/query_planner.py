import json
import re
from dataclasses import dataclass

from cora.core.errors import LlmError
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ChatModel, Message
from cora.core.query_plan import QueryPlan


@dataclass(frozen=True)
class QueryPlanner:
    chat_model: ChatModel
    num_queries: int

    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan:
        messages = _planning_messages(question, sources, self.num_queries)
        try:
            reply = self.chat_model.complete(messages, ())
        except LlmError:
            return QueryPlan(queries=(question,))
        plan = parse_plan(reply.text, sources)
        return plan if plan is not None else QueryPlan(queries=(question,))


_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


def _json_candidate(text: str) -> str:
    fence = _FENCE.search(text)
    return fence.group(1) if fence else text


def parse_plan(text: str, sources: tuple[str, ...]) -> QueryPlan | None:
    try:
        data = json.loads(_json_candidate(text))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    raw_queries = data.get("queries")
    if not isinstance(raw_queries, list) or not all(
        isinstance(q, str) for q in raw_queries
    ):
        return None
    queries = tuple(q.strip() for q in raw_queries if q.strip())
    if not queries:
        return None
    source = data.get("source")
    metadata_filter = (
        MetadataFilter(field="source", value=source)
        if isinstance(source, str) and source in sources
        else None
    )
    return QueryPlan(queries=queries, metadata_filter=metadata_filter)


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
