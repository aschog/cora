from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ModelReply
from cora.core.query_plan import QueryPlan
from cora.core.services.query_planner import QueryPlanner
from fakes import ScriptedChatModel


def test_planner_parses_sub_queries_from_the_model_reply() -> None:
    reply = '{"queries": ["what is protein", "protein basics"], "source": null}'
    model = ScriptedChatModel([ModelReply(text=reply)])
    planner = QueryPlanner(chat_model=model, num_queries=2)

    plan = planner.plan("protein?", sources=())

    assert plan == QueryPlan(queries=("what is protein", "protein basics"))


def test_planner_extracts_a_source_filter_when_the_named_source_exists() -> None:
    reply = '{"queries": ["protein timing"], "source": "protein.md"}'
    model = ScriptedChatModel([ModelReply(text=reply)])
    planner = QueryPlanner(chat_model=model, num_queries=1)

    plan = planner.plan("when to take protein?", sources=("protein.md", "energy.md"))

    assert plan.metadata_filter == MetadataFilter(field="source", value="protein.md")


def test_planner_ignores_a_source_filter_naming_an_unknown_document() -> None:
    reply = '{"queries": ["protein timing"], "source": "ghost.md"}'
    model = ScriptedChatModel([ModelReply(text=reply)])
    planner = QueryPlanner(chat_model=model, num_queries=1)

    plan = planner.plan("q", sources=("protein.md",))

    assert plan.metadata_filter is None
    assert plan.queries == ("protein timing",)
