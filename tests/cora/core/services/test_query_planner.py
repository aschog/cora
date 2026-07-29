from cora.core.errors import LlmError
from cora.core.metadata_filter import MetadataFilter
from cora.core.ports.chat_model import ModelReply
from cora.core.query_plan import QueryPlan
from cora.core.services.query_planner import QueryPlanner, parse_plan
from fakes import FailingChatModel, ScriptedChatModel


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


def test_parse_plan_reads_a_json_fenced_object() -> None:
    text = '```json\n{"queries": ["protein basics"], "source": null}\n```'

    plan = parse_plan(text, sources=())

    assert plan == QueryPlan(queries=("protein basics",))


def test_parse_plan_reads_an_untagged_fenced_object() -> None:
    text = '```\n{"queries": ["protein basics"]}\n```'

    assert parse_plan(text, sources=()) == QueryPlan(queries=("protein basics",))


def test_parse_plan_reads_an_object_wrapped_in_prose() -> None:
    lead = parse_plan('Here is the JSON: {"queries": ["a"]}', sources=())
    trail = parse_plan('{"queries": ["a"]} Hope this helps.', sources=())

    assert lead == QueryPlan(queries=("a",))
    assert trail == QueryPlan(queries=("a",))


def test_parse_plan_keeps_the_source_filter_through_wrapping() -> None:
    text = '```json\n{"queries": ["timing"], "source": "protein.md"}\n```'

    plan = parse_plan(text, sources=("protein.md",))

    assert plan == QueryPlan(
        queries=("timing",),
        metadata_filter=MetadataFilter(field="source", value="protein.md"),
    )


def test_parse_plan_scan_ignores_braces_inside_a_query_string() -> None:
    text = 'Sure: {"queries": ["what about {macros}?"]} done'

    assert parse_plan(text, sources=()) == QueryPlan(queries=("what about {macros}?",))


def test_parse_plan_returns_none_for_malformed_json() -> None:
    assert parse_plan("not json at all", sources=()) is None
    assert parse_plan("I can't help with that.", sources=()) is None
    assert parse_plan("```json\n{queries: nope}\n```", sources=()) is None
    assert parse_plan('{"missing": "queries"}', sources=()) is None
    assert parse_plan('{"queries": []}', sources=()) is None


def test_parse_plan_drops_blank_queries_and_strips_the_rest() -> None:
    plan = parse_plan('{"queries": ["  protein  ", ""]}', sources=())

    assert plan == QueryPlan(queries=("protein",))


def test_parse_plan_falls_back_when_every_query_is_blank() -> None:
    assert parse_plan('{"queries": ["", "   "]}', sources=()) is None


def test_planner_falls_back_to_the_raw_question_on_malformed_json() -> None:
    model = ScriptedChatModel([ModelReply(text="not json")])
    planner = QueryPlanner(chat_model=model, num_queries=3)

    plan = planner.plan("how much protein?", sources=("protein.md",))

    assert plan == QueryPlan(queries=("how much protein?",))


def test_planner_falls_back_on_empty_model_text() -> None:
    model = ScriptedChatModel([ModelReply(text="")])
    planner = QueryPlanner(chat_model=model, num_queries=3)

    plan = planner.plan("protein?", sources=())

    assert plan == QueryPlan(queries=("protein?",))


def test_planner_falls_back_when_the_model_fails() -> None:
    model = FailingChatModel(error=LlmError())
    planner = QueryPlanner(chat_model=model, num_queries=3)

    plan = planner.plan("protein?", sources=("protein.md",))

    assert plan == QueryPlan(queries=("protein?",))
