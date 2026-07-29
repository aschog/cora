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
