"""What a plugin is handed, what it may register, and what it is refused for."""

import logging
from dataclasses import replace

import pytest

from cora.domain.errors import PluginLoadError
from cora.engine.host import DELEGATE_BRIEF, MAY_NOT_DELEGATE
from cora.engine.nesting import collecting
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import INSTRUCTIONS, RULE, TOOL
from cora.ports.plugin import ToolCall
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


@pytest.mark.parametrize("acting", MAY_NOT_DELEGATE)
def test_a_delegated_loop_is_never_offered_a_tool_that_acts(acting: str) -> None:
    """A delegated loop reads and never acts: an effect and a stop-to-ask belong in the
    turn around it, which is where the gate already is."""
    model = _answering(ModelReply(text="Two."))
    passed = add_tool()

    host_for(MODULE, model=model).delegate(
        "Do it.", tools=(passed, replace(passed, name=acting))
    )

    assert model.last_tools is not None
    assert acting not in [tool.name for tool in model.last_tools]


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
