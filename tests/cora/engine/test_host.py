"""What a plugin is handed, what it may register, and what it is refused for."""

import logging

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import PluginLoadError, ToolLoopLimitError
from cora.engine.ask_tool import ASK_TOOL_NAME
from cora.engine.host import DELEGATE_BRIEF, MAX_DELEGATED_ROUNDS
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.nesting import collecting
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import Message, ModelReply, TextSink, unheard
from cora.ports.host import INSTRUCTIONS, RULE, TOOL
from cora.ports.plugin import Tool, ToolCall
from cora.ports.retrieval import RetrievedChunk
from fakes import FakeContextSource, FakeMemory, ScriptedChatModel, add_tool, host_for
from fixture_plugins import RefusesContaining

MODULE = "fixture_plugins.valid"


def _schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {"word": {"type": "string"}},
        "required": ["word"],
    }


def _register_echo(host: object, name: str = "echo") -> None:
    host.register_tool(  # ty: ignore[unresolved-attribute]
        name=name,
        description="Echo one word back.",
        parameter_schema=_schema(),
        run=lambda word: word,
    )


def test_a_registered_tool_is_kept_as_the_tool_the_model_is_offered() -> None:
    host = host_for(MODULE)

    _register_echo(host)

    [entry] = host.registered
    assert (entry.module, entry.kind) == (MODULE, TOOL)
    assert entry.value.name == "echo"
    assert entry.value.run(word="hi") == "hi"


def test_a_registered_rule_and_instructions_are_kept_in_the_order_registered() -> None:
    host = host_for(MODULE)
    rule = RefusesContaining("no")

    host.register_instructions("Be brief.")
    host.register_rule(rule)

    assert [(entry.kind, entry.value) for entry in host.registered] == [
        (INSTRUCTIONS, "Be brief."),
        (RULE, rule),
    ]


def test_every_registration_carries_the_module_that_made_it() -> None:
    """What a refusal quotes back, and what story 6's scope rule will read."""
    host = host_for("cora.plugins.fitness")

    host.register_instructions("Be a coach.")
    _register_echo(host)

    assert {entry.module for entry in host.registered} == {"cora.plugins.fitness"}


def test_a_plugin_that_registers_nothing_registers_nothing() -> None:
    assert host_for(MODULE).registered == []


def test_a_tool_with_no_name_is_refused_by_module() -> None:
    host = host_for(MODULE)

    with pytest.raises(PluginLoadError) as refused:
        _register_echo(host, name="   ")

    assert MODULE in refused.value.user_message
    assert "no name" in refused.value.user_message


def test_one_plugin_registering_a_name_twice_is_refused_by_module() -> None:
    host = host_for(MODULE)
    _register_echo(host)

    with pytest.raises(PluginLoadError) as refused:
        _register_echo(host)

    assert "registered twice" in refused.value.user_message


def test_a_tool_that_cannot_be_called_is_refused() -> None:
    host = host_for(MODULE)

    with pytest.raises(PluginLoadError) as refused:
        host.register_tool(
            name="echo",
            description="Echo.",
            parameter_schema=_schema(),
            run="not callable",  # ty: ignore[invalid-argument-type]
        )

    assert "callable" in refused.value.user_message


def test_a_parameter_schema_that_is_not_json_schema_is_refused() -> None:
    host = host_for(MODULE)

    with pytest.raises(PluginLoadError) as refused:
        host.register_tool(
            name="echo",
            description="Echo.",
            parameter_schema={"type": "integr", "properties": []},
            run=lambda word: word,
        )

    assert "invalid parameter schema" in refused.value.user_message


def test_the_host_hands_over_coras_own_ports_rather_than_copies() -> None:
    """A plugin searching the documents searches the index the uploads went into, and
    what it remembers is what the next turn's brief reads."""
    documents, memory = FakeContextSource(), FakeMemory()

    host = host_for(MODULE, documents=documents, memory=memory)

    assert host.documents is documents
    assert host.memory is memory


def test_a_plugin_searches_the_documents_through_the_host() -> None:
    documents = FakeContextSource()

    host_for(MODULE, documents=documents).documents.search("protein", 3)

    assert (documents.last_query, documents.last_k) == ("protein", 3)


def test_a_plugin_remembers_through_the_host() -> None:
    memory = FakeMemory()

    host = host_for(MODULE, memory=memory)
    assert host.memory is not None
    host.memory.remember("trains on Tuesdays")

    assert [fact.text for fact in memory.recall()] == ["trains on Tuesdays"]


def test_a_deployment_that_keeps_nothing_hands_the_plugin_no_memory() -> None:
    assert host_for(MODULE).memory is None


def test_a_plugin_calls_the_model_through_the_host() -> None:
    model = ScriptedChatModel([ModelReply(text="the answer")])

    reply = host_for(MODULE, model=model).model.complete((), ())

    assert reply.text == "the answer"


def test_a_plugins_log_is_named_for_the_plugin() -> None:
    """So a line in the log says which plugin wrote it, without the plugin saying so."""
    host = host_for("cora.plugins.fitness")

    assert host.log.name == "cora.plugins.fitness"
    assert isinstance(host.log, logging.Logger)


def test_a_plugin_reads_the_settings_named_for_it() -> None:
    host = host_for(MODULE, settings={"units": "metric"})

    assert host.settings["units"] == "metric"


def test_a_plugin_given_no_settings_reads_none() -> None:
    assert dict(host_for(MODULE).settings) == {}


def _answering(*replies: ModelReply) -> ScriptedChatModel:
    return ScriptedChatModel(list(replies))


def test_a_delegated_loop_answers_with_what_the_model_wrote() -> None:
    host = host_for(MODULE, model=_answering(ModelReply(text="Two.")))

    assert host.delegate("What is one and one?") == "Two."


def test_a_delegated_loop_is_briefed_and_asked_the_task() -> None:
    model = _answering(ModelReply(text="Two."))

    host_for(MODULE, model=model).delegate("What is one and one?")

    assert model.last_messages is not None
    assert model.last_messages[0].content == DELEGATE_BRIEF
    assert model.last_messages[1].content == "What is one and one?"


def test_a_delegated_loop_may_search_the_documents() -> None:
    model = _answering(ModelReply(text="Two."))

    host_for(MODULE, model=model).delegate("What do the notes say?")

    assert model.last_tools is not None
    assert [tool.name for tool in model.last_tools] == [SEARCH_TOOL_NAME]


def test_a_delegated_loop_is_offered_the_tools_the_plugin_passed() -> None:
    model = _answering(ModelReply(text="Two."))

    host_for(MODULE, model=model).delegate("Add them.", tools=(add_tool(),))

    assert model.last_tools is not None
    assert [tool.name for tool in model.last_tools] == [SEARCH_TOOL_NAME, "add"]


def test_a_delegated_loop_is_never_offered_a_tool_of_coras_that_acts() -> None:
    """A delegated loop reads. Cora's own writing and stopping tools are not in the set
    it is offered — by construction, since the set is search plus what the plugin
    passed — so an effect and a stop-to-ask stay in the turn, where the gate is."""
    model = _answering(ModelReply(text="Two."))

    host_for(MODULE, model=model).delegate("Do it.", tools=(add_tool(),))

    assert model.last_tools is not None
    offered = [tool.name for tool in model.last_tools]
    assert REMEMBER_TOOL_NAME not in offered
    assert ASK_TOOL_NAME not in offered


def test_a_delegated_loop_runs_the_tools_it_asked_for() -> None:
    model = _answering(
        ModelReply(
            tool_calls=(ToolCall(name="add", arguments={"a": 1, "b": 1}, call_id="c1"),)
        ),
        ModelReply(text="Two."),
    )

    answered = host_for(MODULE, model=model).delegate("Add them.", tools=(add_tool(),))

    assert answered == "Two."
    assert model.completions == 2


def test_a_delegated_loop_reports_its_steps_to_the_call_it_ran_inside() -> None:
    """What makes a nested trace: the loop says what it did, and whoever ran it hangs
    those steps under the call rather than beside it."""
    model = _answering(
        ModelReply(
            tool_calls=(ToolCall(name="add", arguments={"a": 1, "b": 1}, call_id="c1"),)
        ),
        ModelReply(text="Two."),
    )

    with collecting() as taken:
        host_for(MODULE, model=model).delegate("Add them.", tools=(add_tool(),))

    assert [step.summary for step in taken] == [
        "Decided to call add",
        "add(a=1, b=1) → 2",
        "Decided no tool was needed",
    ]


def test_a_delegated_loops_answer_cites_no_number_of_its_own() -> None:
    """The numbers belong to the turn. A loop that handed itself `[1]` would collide
    with the `[1]` the turn already gave the reader, and the page would draw a button
    onto the wrong document."""
    model = _answering(ModelReply(text="Sleep, not volume [1]."))

    answered = host_for(MODULE, model=model).delegate("Why do squats stall?")

    assert answered == "Sleep, not volume."


def test_a_tool_run_inside_a_delegated_loop_keeps_its_own_steps() -> None:
    """A loop that calls a tool which delegates again: what the inner loop did belongs
    under the call that ran it, at whatever depth, and never beside it."""
    inner = ScriptedChatModel([ModelReply(text="the inner answer")])
    outer = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(ToolCall(name="ask_again", arguments={}, call_id="c1"),)
            ),
            ModelReply(text="the outer answer"),
        ]
    )
    inner_host = host_for(MODULE, model=inner)
    again = Tool(
        name="ask_again",
        description="Ask the model again.",
        parameter_schema={"type": "object", "properties": {}},
        run=lambda: inner_host.delegate("and again?"),
    )

    with collecting() as taken:
        host_for(MODULE, model=outer).delegate("Ask.", tools=(again,))

    [call] = [step for step in taken if step.summary.startswith("ask_again(")]
    assert [step.summary for step in call.steps] == ["Decided no tool was needed"]
    assert [step.summary for step in taken] == [
        "Decided to call ask_again",
        "ask_again() → the inner answer",
        "Decided no tool was needed",
    ]


def test_a_loop_may_not_spend_more_rounds_than_the_host_allows() -> None:
    """The budget is the host's: a plugin asking for ten thousand rounds gets the
    ceiling, so one tool call cannot spend a deployment's model bill."""
    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(name="add", arguments={"a": 1, "b": 1}, call_id="c1"),
                )
            )
        ]
        * (MAX_DELEGATED_ROUNDS + 1)
    )

    with pytest.raises(ToolLoopLimitError):
        host_for(MODULE, model=model).delegate(
            "Loop forever.", tools=(add_tool(),), rounds=10_000
        )

    assert model.completions == MAX_DELEGATED_ROUNDS + 1


def test_a_delegated_loop_reads_its_passages_by_document_rather_than_by_number() -> (
    None
):
    """The numbers are the turn's to hand out, so a loop is not shown them at all — it
    is shown which document each passage came from, and can say so in prose that
    survives the answer coming back."""
    documents = FakeContextSource(
        results=[
            RetrievedChunk(
                chunk=Chunk(
                    text="squats stall on sleep",
                    source="notes.md",
                    index=0,
                    offset=0,
                ),
                score=1.0,
            )
        ]
    )
    model = _answering(
        ModelReply(
            tool_calls=(
                ToolCall(
                    name=SEARCH_TOOL_NAME,
                    arguments={"query": "squats"},
                    call_id="s1",
                ),
            )
        ),
        ModelReply(text="notes.md says squats stall on sleep."),
    )

    answered = host_for(MODULE, documents=documents, model=model).delegate("Why?")

    assert model.last_messages is not None
    read = model.last_messages[-1].content
    assert "notes.md: squats stall on sleep" in read
    assert "[1]" not in read, "a number the loop cannot hand out is not shown to it"
    assert answered == "notes.md says squats stall on sleep."


def test_stripping_a_number_a_loop_invented_leaves_the_rest_as_written() -> None:
    """Belt and braces over the reading above: a loop that writes a number anyway loses
    it, and loses nothing else — the lines it wrote stay the lines it wrote."""
    model = _answering(ModelReply(text="Two points:\n[1] sleep\n[2] volume"))

    answered = host_for(MODULE, model=model).delegate("List them.")

    assert answered == "Two points:\nsleep\nvolume"


def test_an_answer_that_cited_nothing_comes_back_exactly_as_written() -> None:
    """Only a line a number came out of is tidied. An indented list, a fenced block or
    an aligned table is what the loop wrote, and the outer model reads it as written."""
    written = "- a\n  - a1\n    - a2\n\n```py\ndef f():\n    return 1\n```"
    model = _answering(ModelReply(text=written))

    assert host_for(MODULE, model=model).delegate("Show me.") == written


def test_only_the_line_a_number_left_is_closed_up() -> None:
    model = _answering(ModelReply(text="  sleep [1] matters\n    and so does food"))

    answered = host_for(MODULE, model=model).delegate("Why?")

    assert answered == "  sleep matters\n    and so does food"


def test_a_loop_and_everything_it_delegates_share_one_allowance() -> None:
    """Nesting is not a way to ask again: a loop that delegates again spends the pot the
    outermost one opened, so one tool call costs what the host allows however deep the
    plugin goes."""
    calls: list[str] = []
    inner_host = host_for(MODULE, model=_endlessly(calls, "inner"))
    deeper = Tool(
        name="deeper",
        description="Ask again, one level down.",
        parameter_schema={"type": "object", "properties": {}},
        run=lambda: inner_host.delegate("deeper?"),
    )

    with pytest.raises(ToolLoopLimitError):
        host_for(MODULE, model=_endlessly(calls, "outer")).delegate(
            "Go.", tools=(deeper,)
        )

    assert len(calls) <= MAX_DELEGATED_ROUNDS + 1, (
        f"one allowance across every level, and {len(calls)} rounds were spent"
    )


class _Endless:
    """A model that always asks for one more tool call, so only a budget stops it."""

    def __init__(self, calls: list[str], name: str, tool: str) -> None:
        self.calls = calls
        self.name = name
        self.tool = tool

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        self.calls.append(self.name)
        return ModelReply(
            tool_calls=(
                ToolCall(name=self.tool, arguments={}, call_id=f"c{len(self.calls)}"),
            )
        )


def _endlessly(calls: list[str], name: str) -> _Endless:
    return _Endless(calls, name, tool="deeper" if name == "outer" else "nothing")
