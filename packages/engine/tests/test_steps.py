import dataclasses
from dataclasses import dataclass, replace

import pytest

from cora.domain.agent_state import AgentState
from cora.domain.chunk import Chunk
from cora.domain.citations import NO_MATCHES, Source
from cora.domain.errors import (
    InputRejectedError,
    LlmError,
    RetrievalError,
    ToolLoopLimitError,
)
from cora.domain.trace import ModelDecision, ToolUse
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.engine.steps import (
    REMEMBERED_HEADING,
    UNTRUSTED_NOTICE,
    GroundStep,
    ModelStep,
    PrepareStep,
    Router,
    ToolStep,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import EmptyInputRule, ValidationPipeline
from cora.ports.chat_model import Message, ModelReply
from cora.ports.graph import DONE, GROUND, TOOLS
from cora.ports.memory import Memory
from cora.ports.plugin import Tool, ToolCall
from cora.ports.retrieval import RetrievedChunk
from fakes import (
    FailingChatModel,
    FakeContextSource,
    FakeMemory,
    ScriptedChatModel,
    add_tool,
)


def _hit(
    source: str, text: str = "protein builds muscle", score: float = 1.0
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=score
    )


def _asked(*calls: ToolCall, known: tuple[Source, ...] = ()) -> AgentState:
    reply = Message(role="assistant", content="", tool_calls=calls)
    return {"messages": [reply], "sources": list(known)}


def _search_call(call_id: str, name: str = SEARCH_TOOL_NAME) -> ToolCall:
    return ToolCall(name=name, arguments={"query": "protein"}, call_id=call_id)


def _searcher(*hits: RetrievedChunk, name: str = SEARCH_TOOL_NAME):
    tool = search_tool(FakeContextSource(list(hits)), top_k=3)
    return dataclasses.replace(tool, name=name)


def _add_call(call_id: str, a: int = 1, b: int = 2) -> ToolCall:
    return ToolCall(name="add", arguments={"a": a, "b": b}, call_id=call_id)


def test_a_tool_call_runs_and_answers_the_model_it_was_asked_by() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    [message] = partial["messages"]
    assert message.role == "tool"
    assert message.tool_call_id == "c1"


def test_a_call_is_traced_with_the_tool_and_the_arguments_it_ran_with() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    [used] = partial["trace"]
    assert used == ToolUse(
        name="add", arguments={"a": 1, "b": 2}, outcome="3", detail="3"
    )


def test_a_citable_payload_is_traced_by_its_own_summary_and_its_block() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1")))

    [used] = partial["trace"]
    assert (
        used.summary == f'{SEARCH_TOOL_NAME}(query="protein") → 1 passage from note.md'
    )
    assert used.detail == "[1] note.md: protein builds muscle"
    assert "untrusted" not in used.detail.lower()


def test_a_failed_call_is_traced_as_failed_and_carries_the_error() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(ToolCall(name="nope", arguments={}, call_id="c1")))

    [used] = partial["trace"]
    assert used.failed
    assert "nope" in used.summary


def test_every_call_of_a_round_is_traced_in_order() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1"), _add_call("c2", a=3, b=4)))

    assert [used.summary for used in partial["trace"]] == [
        "add(a=1, b=2) → 3",
        "add(a=3, b=4) → 7",
    ]


def test_a_payload_that_registers_nothing_is_fed_back_as_it_renders() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    [message] = partial["messages"]
    assert message.content == "3"
    assert partial["sources"] == []


def test_the_model_gets_the_passages_labelled_as_untrusted_data() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1")))

    [used] = partial["trace"]
    [message] = partial["messages"]
    notice, _, body = message.content.partition("[1]")
    assert "untrusted" in notice.lower()
    assert "instructions" in notice.lower()
    assert body in message.content
    assert "untrusted" not in used.detail.lower()


def test_passages_are_labelled_even_when_they_add_no_new_source() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1"), known=(Source(1, "note.md"),)))

    assert partial["sources"] == []
    [message] = partial["messages"]
    assert "untrusted" in message.content.lower()
    assert "[1] note.md" in message.content


def test_the_sources_it_registered_land_in_the_partial_state() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("note.md")),)))

    partial = step(_asked(_search_call("c1")))

    assert partial["sources"] == [Source(1, "note.md")]


def test_a_later_retrieval_in_the_same_run_continues_the_numbering() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("later.md")),)))

    partial = step(_asked(_search_call("c2"), known=(Source(1, "note.md"),)))

    assert partial["sources"] == [Source(2, "later.md")]
    [used] = partial["trace"]
    assert "[2] later.md" in used.detail


def test_any_tool_returning_a_citable_payload_is_registered_the_same_way() -> None:
    runtime = ToolRuntime(
        tools=(
            _searcher(_hit("note.md")),
            _searcher(_hit("diary.md"), name="recall"),
        )
    )

    partial = ToolStep(runtime)(
        _asked(_search_call("c1"), _search_call("c2", name="recall"))
    )

    assert partial["sources"] == [Source(1, "note.md"), Source(2, "diary.md")]
    searched, recalled = partial["trace"]
    assert "[1] note.md" in searched.detail
    assert "[2] diary.md" in recalled.detail


def test_several_calls_in_one_round_all_run_in_order() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1"), _add_call("c2", a=3, b=4)))

    assert [m.tool_call_id for m in partial["messages"]] == ["c1", "c2"]
    assert [m.content for m in partial["messages"]] == ["3", "7"]


def test_an_unknown_tool_comes_back_as_a_tool_message() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(ToolCall(name="nope", arguments={}, call_id="c1")))

    [message] = partial["messages"]
    assert message.role == "tool"
    assert "nope" in message.content


def test_malformed_arguments_come_back_as_a_tool_message() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(
        _asked(ToolCall(name="add", arguments={"a": "one", "b": 2}, call_id="c1"))
    )

    [message] = partial["messages"]
    assert "invalid arguments" in message.content


def _model_step(*replies: ModelReply) -> ModelStep:
    return ModelStep(
        chat_model=ScriptedChatModel(list(replies)),
        tools=(add_tool(),),
        max_history_turns=20,
    )


def _asking(text: str = "add 1 and 2") -> AgentState:
    return {
        "messages": [Message(role="user", content=text)],
        "brief": "SYS",
        "turn_start": 0,
    }


def test_the_step_sends_the_brief_and_the_turn_and_the_bound_tools() -> None:
    model = ScriptedChatModel([ModelReply(text="The sum is 3.")])
    step = ModelStep(chat_model=model, tools=(add_tool(),), max_history_turns=20)
    state = _asking()

    partial = step(state)

    assert model.last_messages == (
        Message(role="system", content="SYS"),
        *state["messages"],
    )
    assert model.last_tools == (add_tool(),)
    [reply] = partial["messages"]
    assert reply.role == "assistant"
    assert reply.content == "The sum is 3."


def test_the_step_sends_a_projection_never_the_raw_transcript() -> None:
    """The thread holds every round ever run; the prompt holds this turn and the
    words of the ones before it."""
    model = ScriptedChatModel([ModelReply(text="ok")])
    step = ModelStep(chat_model=model, tools=(), max_history_turns=20)
    stub = Message(role="assistant", content="", tool_calls=(_add_call("old"),))
    state: AgentState = {
        "messages": [
            Message(role="user", content="last turn"),
            stub,
            Message(role="tool", content="3", tool_call_id="old"),
            Message(role="assistant", content="It was 3."),
            Message(role="user", content="this turn"),
        ],
        "brief": "SYS",
        "turn_start": 4,
    }

    step(state)

    assert model.last_messages is not None
    assert [m.role for m in model.last_messages] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert stub not in model.last_messages


def test_a_tool_calling_reply_keeps_its_calls_ahead_of_the_rounds_tool_messages() -> (
    None
):
    state = _asking()
    from_model = _model_step(ModelReply(tool_calls=(_add_call("c1"),)))(state)
    asked: AgentState = {
        **state,
        "messages": [*state["messages"], *from_model["messages"]],
    }

    from_tools = ToolStep(ToolRuntime(tools=(add_tool(),)))(asked)

    transcript = [*asked["messages"], *from_tools["messages"]]
    assert [m.role for m in transcript] == ["user", "assistant", "tool"]
    assert transcript[1].tool_calls == (_add_call("c1"),)


def test_a_final_reply_sets_the_answer_and_a_tool_calling_one_does_not() -> None:
    final = _model_step(ModelReply(text="The sum is 3."))(_asking())
    calling = _model_step(ModelReply(tool_calls=(_add_call("c1"),)))(_asking())

    assert final["answer"] == "The sum is 3."
    assert "answer" not in calling


def test_a_tool_calling_reply_is_traced_as_the_decision_it_was() -> None:
    calling = ModelReply(text="Let me add those.", tool_calls=(_add_call("c1"),))

    partial = _model_step(calling)(_asking())

    assert partial["trace"] == [
        ModelDecision(detail="Let me add those.", tools=("add",))
    ]


def test_a_final_reply_is_traced_without_repeating_the_answer() -> None:
    partial = _model_step(ModelReply(text="The sum is 3."))(_asking())

    assert partial["trace"] == [ModelDecision()]


def test_each_visit_appends_exactly_one_assistant_message() -> None:
    """Which is what a round is counted by: no separate counter to fall out of step
    with the transcript, and none to carry over into the next turn."""
    step = _model_step(ModelReply(text="one"), ModelReply(text="two"))

    assert [m.role for m in step(_asking())["messages"]] == ["assistant"]
    assert [m.role for m in step(_asking())["messages"]] == ["assistant"]


def test_an_llm_error_from_the_chat_model_propagates_unchanged() -> None:
    error = LlmError()
    step = ModelStep(chat_model=FailingChatModel(error), tools=(), max_history_turns=20)

    with pytest.raises(LlmError) as exc_info:
        step(_asking())

    assert exc_info.value is error


def _prepare(prompt: str = "SYS", memory: Memory | None = None) -> PrepareStep:
    return PrepareStep(
        validation=ValidationPipeline((EmptyInputRule(),), ()),
        system_prompt=prompt,
        memory=memory or FakeMemory(),
    )


class _RecordingValidator:
    def __init__(self) -> None:
        self.seen: str | None = None

    def validate(self, user_input: str) -> str:
        self.seen = user_input
        return user_input


def test_an_invalid_question_is_rejected() -> None:
    step = _prepare()

    with pytest.raises(InputRejectedError):
        step({"question": "   "})


def test_the_validator_sees_the_question_alone() -> None:
    validator = _RecordingValidator()
    step = replace(_prepare(), validation=validator)

    step({"question": "What about protein?"})

    assert validator.seen == "What about protein?"


def test_the_step_appends_the_validated_question_and_nothing_else() -> None:
    """The thread already holds what was said before; a turn adds one message to
    it, so a ten-turn conversation carries one brief and not ten."""
    partial = _prepare()({"question": "What was my weight?"})

    assert partial["messages"] == [Message(role="user", content="What was my weight?")]


def test_the_turn_starts_where_the_transcript_had_reached() -> None:
    said = [
        Message(role="user", content="earlier"),
        Message(role="assistant", content="quite"),
    ]

    partial = _prepare()({"question": "q", "messages": said})

    assert partial["turn_start"] == 2


def test_the_brief_carries_the_plugin_prompt_and_the_agents_rules() -> None:
    partial = _prepare(prompt="You are a fitness coach.")({"question": "q"})

    assert "You are a fitness coach." in partial["brief"]
    assert SEARCH_TOOL_NAME in partial["brief"]
    assert "[n]" in partial["brief"]


def test_the_step_opens_the_turn_by_dropping_what_the_last_one_left() -> None:
    """An answer and a held answer are one turn's business. Carried over, the gate
    would think it had already looked and the run would return a stale answer."""
    partial = _prepare()(
        {"question": "q", "answer": "last turn's", "answer_in_hand": "last turn's"}
    )

    assert partial["answer"] == ""
    assert partial["answer_in_hand"] == ""


def test_the_brief_carries_every_remembered_fact_beneath_the_plugin_prompt() -> None:
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))

    partial = _prepare(prompt="You are a coach.", memory=memory)({"question": "q"})

    brief = partial["brief"]
    assert brief.index("You are a coach.") < brief.index("trains on Tuesdays")
    assert "is vegetarian" in brief


def test_nothing_remembered_leaves_no_memory_section_in_the_brief() -> None:
    partial = _prepare(memory=FakeMemory())({"question": "q"})

    assert REMEMBERED_HEADING not in partial["brief"]


def test_the_rules_tell_the_model_to_remember_what_the_user_shares() -> None:
    partial = _prepare()({"question": "q"})

    assert REMEMBER_TOOL_NAME in partial["brief"]


def _replied(
    *calls: ToolCall, text: str = "The sum is 3.", rounds: int = 1
) -> AgentState:
    """A turn that has had `rounds` model calls, the last of them this reply. Rounds
    are counted off the transcript, so a test states them by saying what was said."""
    earlier = [
        Message(role="assistant", content=f"round {number}")
        for number in range(1, rounds)
    ]
    return {
        "messages": [
            *earlier,
            Message(role="assistant", content=text, tool_calls=calls),
        ],
        "turn_start": 0,
    }


def _after_searching(state: AgentState) -> AgentState:
    searched = Message(role="assistant", content="", tool_calls=(_search_call("c1"),))
    return {**state, "messages": [searched, *state["messages"]]}


def test_a_final_reply_routes_to_done() -> None:
    assert Router(max_tool_rounds=8)(_replied()) == DONE


def test_a_tool_calling_reply_under_budget_routes_to_the_tools() -> None:
    assert Router(max_tool_rounds=8)(_replied(_add_call("c1"))) == TOOLS


def test_a_tool_calling_reply_at_the_round_budget_gives_up_kindly() -> None:
    with pytest.raises(ToolLoopLimitError) as exc_info:
        Router(max_tool_rounds=2)(_replied(_add_call("c1"), rounds=2))

    assert exc_info.value.user_message == ToolLoopLimitError().user_message


def test_an_answer_from_an_earlier_round_can_no_longer_end_the_run() -> None:
    asking_again: AgentState = {**_replied(_add_call("c1")), "answer": "stale"}

    assert Router(max_tool_rounds=8)(asking_again) == TOOLS


def test_an_ungrounded_answer_is_sent_back_when_the_plugin_asks_for_it() -> None:
    router = Router(max_tool_rounds=8, grounded=True)

    assert router(_replied()) == GROUND


def test_an_answer_that_followed_a_search_is_grounded_enough() -> None:
    router = Router(max_tool_rounds=8, grounded=True)

    assert router(_after_searching(_replied())) == DONE


def test_an_answer_the_tools_already_worked_for_is_left_alone() -> None:
    """The gate is for an answer the model made up, not for one a calculator
    produced: a plugin's own tools are as good a ground as its documents."""
    router = Router(max_tool_rounds=8, grounded=True)
    calculated = Message(role="assistant", content="", tool_calls=(_add_call("c1"),))
    state: AgentState = {
        "messages": [calculated, *_replied()["messages"]],
        "turn_start": 0,
    }

    assert router(state) == DONE


def test_the_gate_reads_the_transcript_not_the_trace() -> None:
    router = Router(max_tool_rounds=8, grounded=True)
    only_traced: AgentState = {
        **_replied(),
        "trace": [ToolUse(name=SEARCH_TOOL_NAME, outcome="1 passage")],
    }

    assert router(only_traced) == GROUND


def test_the_gate_fires_once_so_a_run_can_never_loop_on_it() -> None:
    router = Router(max_tool_rounds=8, grounded=True)

    assert router({**_replied(rounds=2), "reconsidered": True}) == DONE


def test_a_plugin_that_asks_for_no_grounding_goes_straight_to_done() -> None:
    assert Router(max_tool_rounds=8)(_replied()) == DONE


def test_a_second_look_costs_one_round_now_that_the_gate_does_the_searching() -> None:
    """The gate no longer spends a round on tools, so the room a second look needs
    is the one model call that reads the evidence."""
    assert Router(max_tool_rounds=2, grounded=True)(_replied()) == GROUND


def test_a_budget_with_no_room_for_the_second_look_still_leaves_it_alone() -> None:
    assert Router(max_tool_rounds=1, grounded=True)(_replied()) == DONE


def test_an_empty_final_answer_does_not_circle_the_gate_forever() -> None:
    """The gate having looked and the gate holding something are different facts: an
    answer of no words is still an answer it has already reconsidered."""
    router = Router(max_tool_rounds=8, grounded=True)

    state: AgentState = {
        **_replied(text=""),
        "answer_in_hand": "",
        "reconsidered": True,
    }

    assert router(state) == DONE


def test_the_round_budget_belongs_to_the_turn_not_the_conversation() -> None:
    """Rounds are counted from where the turn began, so a long conversation cannot
    exhaust a turn's budget before the turn has asked for anything."""
    spent = [Message(role="assistant", content=f"turn {n}") for n in range(1, 9)]
    this_turn: AgentState = {
        "messages": [*spent, *_replied(_add_call("c1"))["messages"]],
        "turn_start": len(spent),
    }

    assert Router(max_tool_rounds=2)(this_turn) == TOOLS


def test_a_search_from_an_earlier_turn_is_not_this_turns_tool_use() -> None:
    """Otherwise the gate would fall silent for the rest of the conversation after
    the first search it ever made."""
    router = Router(max_tool_rounds=8, grounded=True)
    last_turn = [
        Message(role="user", content="what do my notes say?"),
        Message(role="assistant", content="", tool_calls=(_search_call("c1"),)),
        Message(role="tool", content="[1] note.md: protein", tool_call_id="c1"),
        Message(role="assistant", content="They say protein [1]."),
    ]
    this_turn: AgentState = {
        "messages": [*last_turn, *_replied()["messages"]],
        "turn_start": len(last_turn),
    }

    assert router(this_turn) == GROUND


def _gate(*hits: RetrievedChunk, reminder: str = "Weigh these.") -> GroundStep:
    return GroundStep(
        reminder=reminder, context_source=FakeContextSource(list(hits)), top_k=3
    )


def test_the_step_searches_the_question_and_hands_the_passages_to_the_model() -> None:
    """The second look weighs evidence rather than an instruction: the gate runs the
    search itself, so a model that ignores being told to look still sees what the
    documents say."""
    source = FakeContextSource([_hit("protein.md")])
    step = GroundStep(reminder="Weigh these.", context_source=source, top_k=3)

    partial = step({"question": "how much protein?"})

    assert source.last_query == "how much protein?"
    assert source.last_k == 3
    [message] = partial["messages"]
    assert message.role == "system"
    assert message.content.startswith("Weigh these.")
    assert "[1] protein.md: protein builds muscle" in message.content


def test_the_nudge_holds_on_to_the_answer_it_is_second_guessing() -> None:
    """Holding the answer is what tells a failed second look apart from a failure
    after one: nothing has to count rounds to know which happened."""
    held = _gate()({"question": "anything?", "answer": "Off the cuff."})

    assert held["answer_in_hand"] == "Off the cuff."


def test_the_passages_reach_the_model_behind_the_untrusted_data_label() -> None:
    partial = _gate(_hit("protein.md"))({"question": "how much protein?"})

    [message] = partial["messages"]
    assert UNTRUSTED_NOTICE in message.content
    assert message.content.index(UNTRUSTED_NOTICE) < message.content.index("[1]")


def test_the_sources_it_found_are_numbered_after_the_ones_already_known() -> None:
    partial = _gate(_hit("protein.md"))(
        {"question": "how much protein?", "sources": [Source(1, "creatine.md")]}
    )

    assert partial["sources"] == [Source(2, "protein.md")]


def test_a_search_that_matches_nothing_says_so_instead_of_implying_evidence() -> None:
    partial = _gate()({"question": "hi there!"})

    [message] = partial["messages"]
    assert NO_MATCHES in message.content
    assert partial["sources"] == []


def test_a_passage_too_far_from_the_question_is_not_evidence() -> None:
    """Top-k always returns something, so a greeting gets the nearest passage however
    far it is. Measured with the real embedder, a question in the documents' subject
    scores 0.34 to 0.69 and small talk -0.02 to 0.08; below the floor there is
    nothing to weigh, and the answer stands."""
    partial = _gate(_hit("protein.md", score=0.02))({"question": "hi there!"})

    [message] = partial["messages"]
    assert NO_MATCHES in message.content
    assert partial["sources"] == []


def test_a_passage_near_enough_to_the_question_is_weighed() -> None:
    partial = _gate(_hit("protein.md", score=0.34))({"question": "how much protein?"})

    [message] = partial["messages"]
    assert "[1] protein.md" in message.content


def test_a_gate_whose_own_search_fails_keeps_the_answer_and_says_the_look_failed() -> (
    None
):
    """The search is the gate's own now, so its failure is the gate's: losing a good
    answer to a round nothing asked for is the one thing the gate must never do."""
    step = GroundStep(reminder="Weigh these.", context_source=_BrokenSource(), top_k=3)

    partial = step({"question": "how much protein?", "answer": "Off the cuff."})

    assert partial["answer_in_hand"] == "Off the cuff."
    assert partial["sources"] == []
    [recorded] = partial["trace"]
    assert recorded.failed
    [message] = partial["messages"]
    assert NO_MATCHES in message.content


class _BrokenSource:
    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        raise RetrievalError


def test_the_trace_names_the_search_the_gate_ran_and_what_came_back() -> None:
    """A citation in the revised answer has to have a visible origin: the gate did
    the searching, so the step it records is the one that found the passages."""
    partial = _gate(_hit("protein.md"))({"question": "how much protein?"})

    [step] = partial["trace"]
    assert (
        step.summary
        == "Checked the documents and asked again → 1 passage from protein.md"
    )
    assert step.detail == "[1] protein.md: protein builds muscle"


def test_a_gate_that_found_nothing_says_so_in_the_trace() -> None:
    partial = _gate()({"question": "hi there!"})

    [step] = partial["trace"]
    assert step.summary == f"Checked the documents and asked again → {NO_MATCHES}"


@dataclass(frozen=True)
class _Booking:
    """A plugin payload that happens to have a `register` of its own."""

    member: str

    def register(self, session: str) -> str:
        return f"{self.member} is in {session}"


_BOOKING_TOOL = Tool(
    name="book",
    description="Book a session.",
    parameter_schema={"type": "object", "properties": {}},
    run=lambda: _Booking("Ada"),
)


def test_a_payload_that_only_looks_citable_is_fed_back_untouched() -> None:
    step = ToolStep(ToolRuntime(tools=(_BOOKING_TOOL,)))

    partial = step(_asked(ToolCall(name="book", arguments={}, call_id="c1")))

    assert partial["sources"] == []
    [message] = partial["messages"]
    assert message.content == "\"_Booking(member='Ada')\""
    [used] = partial["trace"]
    assert used.detail == message.content
