import dataclasses
from dataclasses import replace
from typing import Any

import pytest

from cora.domain.agent_state import AgentState
from cora.domain.approval import Proposed
from cora.domain.card import ActionOffered, Answer, Asks, Card, FieldAsked
from cora.domain.chunk import Chunk
from cora.domain.citations import Citation
from cora.domain.errors import (
    InputRejectedError,
    LlmError,
    ToolLoopLimitError,
)
from cora.domain.trace import (
    EffectSettled,
    ModelDecision,
    ScopeSettled,
    StepEntered,
)
from cora.engine import keeping
from cora.engine.ask_tool import (
    ASK_FOR_TOOL_NAME,
    ASK_TOOL_NAME,
    SEND,
)
from cora.engine.plugin_set import Registry
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME, search_tool
from cora.engine.rounds import UNTRUSTED_NOTICE
from cora.engine.steps import (
    AGENT_RULES,
    BROKEN_ASKS,
    CORA_PREAMBLE,
    DECLINED_CALL,
    HELD_AT_SEVERAL,
    ONE_VALUE,
    REFUSED_CALL,
    ROUTED,
    UNFILLED_CALL,
    AnswerStep,
    AskStep,
    FocusStep,
    GateStep,
    ModelStep,
    Named,
    Router,
    RouteStep,
    ScreenStep,
    ToolStep,
    _requested_calls,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.engine.validation import CORA, refuse_nothing_to_answer
from cora.ports.chat_model import Message, ModelReply
from cora.ports.graph import ASK, DONE, Step
from cora.ports.host import (
    ANSWERING,
    BRIEFING,
    CALLING,
    HANDLER,
    INSTRUCTIONS,
    RETURNING,
    SCREENING,
    TOOL,
    Handler,
    Registration,
    Subscription,
)
from cora.ports.memory import Memory
from cora.ports.pause import Answered
from cora.ports.plugin import Tool, ToolCall, ToolResult
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


def _asked(*calls: ToolCall, known: tuple[Citation, ...] = ()) -> AgentState:
    reply = Message(role="assistant", content="", tool_calls=calls)
    return {"messages": [reply], "citations": list(known)}


def _search_call(call_id: str, name: str = SEARCH_TOOL_NAME) -> ToolCall:
    return ToolCall(name=name, arguments={"query": "protein"}, call_id=call_id)


def _searcher(*hits: RetrievedChunk, name: str = SEARCH_TOOL_NAME):
    tool = search_tool(FakeContextSource(list(hits)), top_k=3)
    return dataclasses.replace(tool, name=name)


def _fetching(name: str = "forecast") -> Tool:
    """A tool that hands back material cora did not write, said at registration rather
    than read off the payload: what a service returned is a plain string like any
    other, so nothing about its shape could have told the turn where it came from."""
    return Tool(
        name=name,
        description="Fetch a forecast.",
        parameter_schema={"type": "object", "properties": {}},
        run=lambda: "Lisbon, 5-7 Sep: 24/17C Fri, 25/18C Sat",
        untrusted=True,
    )


NOTE = Citation(number=1, document="note.md", start=0, end=len("protein builds muscle"))


def _add_call(call_id: str, a: int = 1, b: int = 2) -> ToolCall:
    return ToolCall(name="add", arguments={"a": a, "b": b}, call_id=call_id)


def test_a_tool_call_runs_and_answers_the_model_it_was_asked_by() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(_add_call("c1")))

    [message] = partial["messages"]
    assert message.role == "tool"
    assert message.tool_call_id == "c1"


def test_a_failed_call_is_traced_as_failed_and_carries_the_error() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(_asked(ToolCall(name="nope", arguments={}, call_id="c1")))

    [used] = partial["trace"]
    assert used.failed
    assert "nope" in used.summary


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


def test_a_later_retrieval_in_the_same_run_continues_the_numbering() -> None:
    step = ToolStep(ToolRuntime(tools=(_searcher(_hit("later.md")),)))

    partial = step(_asked(_search_call("c2"), known=(NOTE,)))

    assert partial["citations"] == [
        Citation(2, "later.md", 0, len("protein builds muscle"))
    ]
    [used] = partial["trace"]
    assert "[2] later.md" in used.detail


def test_malformed_arguments_come_back_as_a_tool_message() -> None:
    step = ToolStep(ToolRuntime(tools=(add_tool(),)))

    partial = step(
        _asked(ToolCall(name="add", arguments={"a": "one", "b": 2}, call_id="c1"))
    )

    [message] = partial["messages"]
    assert "invalid arguments" in message.content


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


def test_an_llm_error_from_the_chat_model_propagates_unchanged() -> None:
    error = LlmError()
    step = ModelStep(chat_model=FailingChatModel(error), tools=(), max_history_turns=20)

    with pytest.raises(LlmError) as exc_info:
        step(_asking())

    assert exc_info.value is error


MODULE = "fixture_plugins.valid"


def _subscribed(event: str, handle: Handler, module: str = MODULE) -> Registration:
    return Registration(
        module=module, kind=HANDLER, value=Subscription(event=event, handle=handle)
    )


def _registry(
    instructions: str = "SYS",
    screens: tuple[Handler, ...] = (),
    briefs: tuple[Handler, ...] = (),
) -> Registry:
    """Cora's own screen first, as an assembled app registers it, then the plugin's."""
    return Registry(
        (
            _subscribed(SCREENING, refuse_nothing_to_answer, CORA),
            *(_subscribed(SCREENING, screen) for screen in screens),
            *(_subscribed(BRIEFING, brief) for brief in briefs),
            Registration(module=MODULE, kind=INSTRUCTIONS, value=instructions),
        )
    )


def _screen(instructions: str = "SYS") -> ScreenStep:
    return ScreenStep(registry=_registry(instructions))


def _focus(instructions: str = "SYS", memory: Memory | None = None) -> FocusStep:
    return FocusStep(registry=_registry(instructions), memory=memory or FakeMemory())


def _routing(*offered: str) -> tuple[RouteStep, ScriptedChatModel]:
    """A router over named fields, each with instructions of its own to be outlined."""
    model = ScriptedChatModel([ModelReply(text=offered[0] if offered else "none")])
    return (
        RouteStep(
            chat_model=model,
            available=offered,
            registry=Registry(
                tuple(
                    Registration(
                        module=f"plugins.{scope}",
                        kind=INSTRUCTIONS,
                        value=f"Answer {scope} questions.",
                        scope=scope,
                    )
                    for scope in offered
                )
            ),
        ),
        model,
    )


def test_a_field_the_router_names_is_what_the_turn_runs_under() -> None:
    step, _ = _routing("travel", "fitness")

    assert step({"question": "Which platform?"}) == {
        "scopes": ["travel"],
        "candidates": [],
        "trace": [ScopeSettled(scope="travel", how=ROUTED)],
    }


def _refuses(message: str) -> Handler:
    def screen(question: str) -> str:
        return message

    return screen


def test_an_invalid_question_is_rejected() -> None:
    step = _screen()

    with pytest.raises(InputRejectedError):
        step({"question": "   "})


def test_the_first_handler_to_refuse_in_order_is_what_the_user_reads() -> None:
    """Every loaded plugin's screen runs in the order the plugins were named, so which
    refusal a user sees is decided by the set, not by the handlers racing."""
    step = replace(
        _screen(), registry=_registry(screens=(_refuses("first"), _refuses("second")))
    )

    with pytest.raises(InputRejectedError) as excinfo:
        step({"question": "anything"})

    assert excinfo.value.user_message == "first"


def test_what_a_brief_handler_returned_is_what_the_model_reads() -> None:
    step = replace(
        _focus(),
        registry=_registry(briefs=(lambda brief: f"{brief}\n\nAlso: be brief.",)),
    )

    partial = step({"question": "q"})

    assert partial["brief"].endswith("Also: be brief.")
    assert "SYS" in partial["brief"], "the amendment was handed the brief as it stood"


def test_the_brief_runs_cora_then_the_domains_then_the_users_own_notes() -> None:
    """Rules ahead of the domains, because a domain section is what a plugin author
    wrote and the rules are what cora will not have overridden; the user's notes come
    last, being neither."""
    memory = FakeMemory(("trains on Tuesdays",))
    brief = _focus(instructions="## Coaching\nBe a coach.", memory=memory)(
        {"question": "q"}
    )["brief"]

    assert (
        brief.index(CORA_PREAMBLE)
        < brief.index(AGENT_RULES)
        < brief.index("Be a coach.")
        < brief.index("trains on Tuesdays")
    )


def _replied(
    *calls: ToolCall, text: str = "The sum is 3.", rounds: int = 1
) -> AgentState:
    """A turn that has had `rounds` model calls, the last of them this reply. Rounds are
    counted off the trace, so a test states them by saying what the model decided."""
    earlier = [
        Message(role="assistant", content=f"round {number}")
        for number in range(1, rounds)
    ]
    return {
        "messages": [
            *earlier,
            Message(role="assistant", content=text, tool_calls=calls),
        ],
        "trace": [ModelDecision() for _ in range(rounds)],
        "turn_start": 0,
        "trace_start": 0,
    }


def test_a_final_reply_routes_to_done() -> None:
    assert Router(max_tool_rounds=8)(_replied()) == DONE


def test_a_tool_calling_reply_at_the_round_budget_gives_up_kindly() -> None:
    with pytest.raises(ToolLoopLimitError) as exc_info:
        Router(max_tool_rounds=2)(_replied(_add_call("c1"), rounds=2))

    assert exc_info.value.user_message == ToolLoopLimitError().user_message


# ── stopping to ask ──

ASKED = "Which bodyweight should I treat as current?"
OFFERED = [{"label": "77 kg"}, {"label": "75 kg", "note": "February"}]


def _ask_call(call_id: str = "a1", **arguments: object) -> ToolCall:
    return ToolCall(
        name=ASK_TOOL_NAME,
        arguments={"question": ASKED, "options": OFFERED, **arguments},
        call_id=call_id,
    )


class _Chosen:
    """A pause that answers with whatever it was handed, and keeps what it was shown so
    a test can read what the reader would have been asked."""

    def __init__(self, answer: str | None, **values: object) -> None:
        self.answer = answer
        self.values = values
        self.shown: Asks | None = None

    def __call__(self, asks: Asks) -> Answer:
        self.shown = asks
        return Answer(action=self.answer, values=self.values)


def test_a_reply_calling_ask_user_routes_to_the_ask() -> None:
    assert Router(max_tool_rounds=8)(_replied(_ask_call())) == ASK


def test_the_label_chosen_comes_back_as_the_answer_to_the_call() -> None:
    partial = AskStep(pause=_Chosen("75 kg"))(_asked(_ask_call("a7")))

    [message] = partial["messages"]
    assert (message.role, message.content, message.tool_call_id) == (
        "tool",
        "75 kg",
        "a7",
    )


def test_a_malformed_ask_is_refused_and_never_reaches_the_reader() -> None:
    pause = _Chosen("75 kg")
    unusable = ToolCall(name=ASK_TOOL_NAME, arguments={"question": ASKED}, call_id="a1")

    partial = AskStep(pause=pause)(_asked(unusable))

    [message] = partial["messages"]
    assert "options" in message.content
    assert pause.shown is None, "a broken card is never put in front of the reader"


# ── asking for what cora does not hold ──

WANTED = "Give me the trip and I'll price it."
FIELDS = [
    {"name": "origin", "description": "Where from", "required": True},
    {"name": "depart", "description": "The day you leave", "format": "date"},
]


def _form_call(call_id: str = "f1", **arguments: object) -> ToolCall:
    return ToolCall(
        name=ASK_FOR_TOOL_NAME,
        arguments={"prompt": WANTED, "fields": FIELDS, **arguments},
        call_id=call_id,
    )


def test_the_step_puts_the_card_the_ask_describes() -> None:
    pause = _Chosen(SEND, origin="BER")

    AskStep(pause=pause)(_asked(_form_call()))

    assert pause.shown is not None
    assert pause.shown.card.prompt == WANTED
    assert [field.name for field in pause.shown.card.fields] == ["origin", "depart"]


def test_an_ask_for_one_value_is_refused_and_never_reaches_the_reader() -> None:
    """A form is worth the stop when it settles several things at once. For one value it
    is a box and a button where a sentence would have done, so the model is told to ask
    in its answer — which the reader replies to in the composer."""
    pause = _Chosen(SEND, height="1.75")
    one = _form_call(
        fields=[{"name": "height", "description": "Your height in metres"}]
    )

    partial = AskStep(pause=pause)(_asked(one))

    [message] = partial["messages"]
    assert ONE_VALUE.format(name="height") in message.content
    assert pause.shown is None, "one value is asked for in prose, not on a card"


def test_what_the_reader_wrote_comes_back_as_the_answer_to_the_call() -> None:
    partial = AskStep(pause=_Chosen(SEND, origin="BER", depart="2026-10-01"))(
        _asked(_form_call("f7"))
    )

    [message] = partial["messages"]
    assert message.tool_call_id == "f7"
    assert "'BER'" in message.content and "'2026-10-01'" in message.content


def _contributing(contributed: AgentState) -> Step:
    def step(state: AgentState) -> AgentState:
        return contributed

    return step


def test_a_named_step_marks_the_trace_with_its_name_before_what_it_did() -> None:
    named = Named("screen", _contributing({"trace": [ModelDecision()], "answer": "ok"}))

    contributed = named({"question": "q"})

    assert contributed["trace"] == [StepEntered("screen"), ModelDecision()]
    assert contributed["answer"] == "ok", "the step's own keys travel out untouched"


def test_the_answering_step_settles_the_answer_the_last_round_reached() -> None:
    settled = AnswerStep()(
        {
            "messages": [
                Message(role="user", content="q"),
                Message(role="assistant", content="Let me add those."),
                Message(role="tool", content="3", tool_call_id="c1"),
                Message(role="assistant", content="The sum is 3."),
            ],
            "turn_start": 0,
        }
    )

    assert settled == {"answer": "The sum is 3.", "trace": []}


def test_a_result_handler_cannot_redirect_the_answer_to_another_call() -> None:
    """The call id is the provider's and answers one call. A handler that changed it
    would leave the round's call unanswered and the transcript claiming to answer a call
    nobody made — so what it returns is read for the payload and not for the id."""
    step = ToolStep(
        tool_runtime=ToolRuntime(tools=(add_tool(),)),
        registry=Registry(
            (
                _subscribed(
                    RETURNING,
                    lambda result: replace(result, call_id="not-the-call", payload=99),
                ),
            )
        ),
    )

    partial = step(
        _asked(ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1"))
    )

    [told] = partial["messages"]
    assert told.tool_call_id == "c1"
    assert told.content == "99", "what the handler returned is still what is told"


@pytest.mark.parametrize(
    ("tool", "call"),
    [
        (_searcher(_hit("note.md")), _search_call("s1")),
        (_fetching(), ToolCall(name="forecast", arguments={}, call_id="f1")),
    ],
    ids=["a-passage", "what-a-service-said"],
)
def test_a_result_handler_cannot_strip_the_label_off_material_cora_did_not_write(
    tool: Tool, call: ToolCall
) -> None:
    """A handler replacing the payload with prose of its own has replaced the material,
    not where it came from: what went into this call went in before any handler saw it,
    so what the model is told still arrives behind the notice that says not to take
    orders from it.

    Asked of both sources the label has. They share one line today, which is exactly
    why the second case is here: a reader who splits them again would otherwise take
    the injection defence off a tool that reaches outside and see nothing go red.
    """
    step = ToolStep(
        tool_runtime=ToolRuntime(tools=(tool,)),
        registry=Registry(
            (
                _subscribed(
                    RETURNING,
                    lambda result: ToolResult(
                        call_id=result.call_id, payload=f"sealed: {result.render()}"
                    ),
                ),
            )
        ),
    )

    partial = step(_asked(call))

    [told] = partial["messages"]
    assert UNTRUSTED_NOTICE in told.content
    assert "sealed:" in told.content, "and it is still what the handler returned"


def test_a_call_handler_cannot_rewrite_the_arguments_the_model_asked_for() -> None:
    """A refusing event may refuse its value and may not change it. The arguments are a
    dict inside a frozen call, so a handler is handed a copy of them — one that mutated
    them in place and refused nothing would change what ran, and leave no step saying
    so."""
    ran: list[int] = []
    counting = Tool(
        name="add",
        description="Add one number to nothing.",
        parameter_schema={"type": "object", "properties": {"a": {"type": "integer"}}},
        run=lambda a: ran.append(a) or f"got {a}",
    )

    def tamper(call: ToolCall) -> None:
        call.arguments["a"] = 999
        return None

    step = ToolStep(
        tool_runtime=ToolRuntime(tools=(counting,)),
        registry=Registry((_subscribed(CALLING, tamper),)),
    )

    step(_asked(ToolCall(name="add", arguments={"a": 1}, call_id="c1")))

    assert ran == [1]


BOOKED = "book_it"
DOES = "Book the thing, which cannot be taken back"


def _acting(name: str = BOOKED, effect: bool = True) -> Tool:
    return Tool(
        name=name,
        description=DOES,
        parameter_schema={"type": "object"},
        run=lambda **_: "booked",
        effect=effect,
    )


def _offering(*tools: Tool) -> Registry:
    return Registry(
        tuple(
            Registration(module="fixture_plugins.valid", kind=TOOL, value=tool)
            for tool in tools
        )
    )


def _proposing(*names: str) -> AgentState:
    calls = tuple(
        ToolCall(name=name, arguments={"what": name}, call_id=f"c{at}")
        for at, name in enumerate(names, start=1)
    )
    return {"messages": [Message(role="assistant", content="", tool_calls=calls)]}


def _yes(*call_ids: str) -> Answered:
    def approve(asks: Asks) -> Answer:
        named = asks.card.actions[0].answer
        return Answer(action=named if named in call_ids else None)

    return approve


def test_the_gate_puts_an_effecting_call_to_the_user_as_the_tool_describes_it() -> None:
    """What is approved is this call and not the idea of it, so the proposal carries the
    tool's own words and the arguments the model wrote."""
    seen: list[Asks] = []

    def approve(asks: Asks) -> Answer:
        seen.append(asks)
        return Answer(action=asks.card.actions[0].answer)

    GateStep(registry=_offering(_acting()), approve=approve)(_proposing(BOOKED))

    assert seen == [
        Proposed(call_id="c1", tool=BOOKED, does=DOES, arguments={"what": BOOKED})
    ]


def test_an_approved_call_is_left_for_the_tools_and_the_approval_is_traced() -> None:
    """The gate runs no tool: what it contributes for a yes is the record of the yes,
    and the call goes on to the tools still outstanding."""
    contributed = GateStep(registry=_offering(_acting()), approve=_yes("c1"))(
        _proposing(BOOKED)
    )

    assert contributed.get("messages", []) == [], "nothing settles an approved call"
    assert contributed["trace"] == [
        EffectSettled(tool=BOOKED, does=DOES, approved=True)
    ]


def test_a_declined_call_is_answered_where_it_was_proposed() -> None:
    """Settled here, so the tools never see it and need no notion of approval at all —
    and the model is told, in a `tool` message like any other, so the turn answers."""
    contributed = GateStep(registry=_offering(_acting()), approve=_yes())(
        _proposing(BOOKED)
    )

    assert contributed["messages"] == [
        Message(
            role="tool", content=DECLINED_CALL.format(name=BOOKED), tool_call_id="c1"
        )
    ]
    assert contributed["trace"] == [
        EffectSettled(tool=BOOKED, does=DOES, approved=False)
    ]


# ── the gate fills in what a tool asked the reader for ──

ASKING = "ask_first"
FILL_IN = "Give me the trip."
SEARCH_IT = (
    ActionOffered(label="Search", answer="Search", needs_valid=True),
    ActionOffered(label="Not now", answer=None),
)
TRIP = Card(
    prompt=FILL_IN,
    fields=(
        FieldAsked(name="origin", required=True),
        FieldAsked(name="depart"),
    ),
    actions=SEARCH_IT,
)
ONE_VALUE_CARD = Card(
    prompt=FILL_IN,
    fields=(FieldAsked(name="origin", required=True),),
    actions=SEARCH_IT,
)


def _gathering(effect: bool = False) -> Tool:
    return Tool(
        name=ASKING,
        description=DOES,
        parameter_schema={
            "type": "object",
            "properties": {"origin": {"type": "string"}},
            "required": ["origin"],
        },
        run=lambda **_: "searched",
        effect=effect,
        asks=lambda arguments: None if arguments.get("origin") else TRIP,
    )


def _filled(origin: str | None) -> Answered:
    def answer(asks: Asks) -> Answer:
        if origin is None:
            return Answer(action=None)
        return Answer(action="Search", values={"origin": origin})

    return answer


def test_a_tool_that_asks_puts_its_card_before_the_call_is_made() -> None:
    """A card built by the tool out of its own schema, put by the gate — which runs no
    tool, so nothing has happened while the reader fills it in."""
    seen: list[Asks] = []

    def answer(asks: Asks) -> Answer:
        seen.append(asks)
        return Answer(action="Search", values={"origin": "BER"})

    GateStep(registry=_offering(_gathering()), approve=answer)(_proposing(ASKING))

    assert [asks.card for asks in seen] == [TRIP]


def test_the_values_the_reader_wrote_are_what_the_tools_are_handed() -> None:
    """What runs is what a person stated. Contributed as state rather than written into
    the transcript: a call the model made is what the model said."""
    state = _proposing(ASKING)
    contributed = GateStep(registry=_offering(_gathering()), approve=_filled("BER"))(
        state
    )

    assert contributed["messages"] == [], "nothing settles a call that is about to run"
    assert contributed["filled"] == {"c1": {"origin": "BER"}}
    # The keys a step contributes; `messages` accumulates in the graph, so it is left
    # as it stands rather than replaced by the empty list the gate returned.
    [call] = _requested_calls({**state, "filled": contributed["filled"]})
    assert call.arguments == {"what": ASKING, "origin": "BER"}
    assert call.call_id == "c1", "the call is the one the model made, filled in"


def _keeper(name: str = "keep", note: str = "note", text: str | None = "Kyoto") -> Tool:
    """A tool that keeps something while its own call runs, as a plugin's does."""

    def run() -> str:
        keeping.keep("keeper", note, text)
        return f"kept {text}"

    return Tool(
        name=name,
        description="Keep a note.",
        parameter_schema={"type": "object", "properties": {}},
        run=run,
    )


def _call(name: str, call_id: str = "c1") -> ToolCall:
    return ToolCall(name=name, arguments={}, call_id=call_id)


def test_what_a_call_kept_is_in_the_state_the_step_contributes() -> None:
    step = ToolStep(ToolRuntime(tools=(_keeper(),)))

    contributed = step(_asked(_call("keep")))

    assert contributed["kept"] == {"keeper": {"note": "Kyoto"}}


def _answering(handle: Handler, scope: str | None = None) -> Registry:
    return Registry(
        (
            Registration(
                module="checker",
                kind=HANDLER,
                value=Subscription(event=ANSWERING, handle=handle),
                scope=scope,
            ),
        )
    )


def _settled(registry: Registry, said: str = "Call 555-0134.") -> AgentState:
    return AnswerStep(registry=registry)(
        {"messages": [Message(role="assistant", content=said)]}
    )


def test_a_handler_is_offered_the_answer_and_what_it_returns_is_settled() -> None:
    contributed = _settled(_answering(lambda answer: answer.replace("555-0134", "x")))

    assert contributed["answer"] == "Call x."


def _raising(_: dict[str, Any]) -> Card:
    raise RuntimeError("the key is hunter2")


def test_a_card_the_reader_gave_nothing_to_leaves_the_call_unrun() -> None:
    """A tool that asked and was told nothing is not run on the arguments it asked
    about: the round is told so, and still has an answer to give."""
    contributed = GateStep(registry=_offering(_gathering()), approve=_filled(None))(
        _proposing(ASKING)
    )

    [told] = contributed["messages"]
    assert told.tool_call_id == "c1"
    assert told.content == UNFILLED_CALL.format(name=ASKING)


def test_a_card_asking_for_one_value_is_refused_and_never_put() -> None:
    """One value is a sentence, not a form. The call is refused the way a broken `asks`
    is — the round is told what to do instead, and nothing stops the reader."""
    seen: list[Asks] = []

    def answer(asks: Asks) -> Answer:
        seen.append(asks)
        return Answer(action="Search", values={"origin": "BER"})

    asking_for_one = replace(_gathering(), asks=lambda _: ONE_VALUE_CARD)

    contributed = GateStep(registry=_offering(asking_for_one), approve=answer)(
        _proposing(ASKING)
    )

    assert seen == [], "a one-field card is never put in front of the reader"
    [told] = contributed["messages"]
    assert told.content == REFUSED_CALL.format(
        name=ASKING, reason=ONE_VALUE.format(name="origin")
    )
    assert contributed["filled"] == {}


def test_a_plugin_whose_asks_breaks_costs_the_call_and_not_the_turn() -> None:
    """The gate is a step of the core, so a plugin that broke inside it is contained the
    way a refusing handler is: the round is told, and the turn still answers."""
    broken = replace(_gathering(), asks=_raising)

    contributed = GateStep(registry=_offering(broken), approve=_filled("BER"))(
        _proposing(ASKING)
    )

    [told] = contributed["messages"]
    assert told.content == REFUSED_CALL.format(name=ASKING, reason=BROKEN_ASKS)
    assert contributed["filled"] == {}


HELD_THREE_WAYS = (
    "bodyweight 77 kg, from the intake form on 17 August",
    "bodyweight 75 kg, from the coach notes in February",
    "bodyweight 85 kg, from the physio letter",
)


def _brief_over(facts: tuple[str, ...]) -> str:
    return _focus(memory=FakeMemory(facts))({"question": "q"})["brief"]


def test_a_fact_the_notes_hold_at_several_values_is_named_as_one() -> None:
    """Cora reads its own notes rather than leaving the model to notice: three weights
    under one subject is a shape it can see, and the model was told to spot it and did
    not — reliably enough to matter, across three of them.

    What it cannot see is whether the answer turns on it, which is why this states the
    conflict and leaves the asking to the rule above.
    """
    brief = _brief_over(HELD_THREE_WAYS)

    assert HELD_AT_SEVERAL.format(subject="bodyweight", count=3) in brief
    assert ASK_TOOL_NAME in brief


def test_notes_that_agree_are_not_reported_as_a_conflict() -> None:
    """The line costs the model attention, so it is absent where there is nothing to
    settle — including where two notes share a subject and say the same thing."""
    settled = (
        "bodyweight 75 kg, from the coach notes",
        "bodyweight 75 kg, from the intake form",
        "trains four times a week",
    )

    assert "held at" not in _brief_over(settled).lower()
    assert "held at" not in _brief_over(HELD_THREE_WAYS[:1]).lower()
