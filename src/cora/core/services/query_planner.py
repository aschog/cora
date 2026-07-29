import json
from dataclasses import dataclass

from cora.core.ports.chat_model import ChatModel, Message
from cora.core.query_plan import QueryPlan


@dataclass(frozen=True)
class QueryPlanner:
    chat_model: ChatModel
    num_queries: int

    def plan(self, question: str, sources: tuple[str, ...]) -> QueryPlan:
        messages = _planning_messages(question, sources, self.num_queries)
        reply = self.chat_model.complete(messages, ())
        return parse_plan(reply.text)


def parse_plan(text: str) -> QueryPlan:
    data = json.loads(text)
    return QueryPlan(queries=tuple(data["queries"]))


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
