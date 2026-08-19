import re
from dataclasses import dataclass

import pytest
from streamlit.testing.v1 import AppTest

from app_builder import assembled, indexed
from apptest import page_text
from cora.app.assembly import App
from cora.domain.chat_result import ChatResult
from cora.domain.chunk import Chunk
from cora.domain.conversation import Turn
from cora.domain.errors import (
    ConfigurationError,
    ConversationStoreError,
    EmptyDocumentError,
    InputRejectedError,
    LlmError,
    MemoryStoreError,
    PluginLoadError,
    RetrievalError,
)
from cora.engine.memory_tool import REMEMBER_TOOL_NAME
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.frontends.streamlit.chat import (
    APP_NAME,
    NO_SESSIONS,
    NOTHING_REMEMBERED,
    RAIL_PANELS,
    REMEMBER_HEADING,
    TAGLINE,
)
from cora.ports.chat_model import ChatModel, ModelReply, unheard
from cora.ports.plugin import Plugin, ToolCall
from cora.ports.retrieval import Retriever
from fakes import (
    FailingChatModel,
    FailingConversations,
    FailingMemory,
    FakeConversations,
    FakeMemory,
    FakeRetriever,
    ReadOnlyMemory,
    ScriptedChatModel,
    UnopenableSessions,
    add_tool,
)
from fixture_plugins import make_plugin


def _app(chat_model: ChatModel, plugin: Plugin | None = None) -> App:
    return assembled(chat_model=chat_model, plugin=plugin)


class _CountingRetriever(FakeRetriever):
    """Counts ingest attempts: ``add_file`` asks ``contains`` before any work."""

    def __init__(self) -> None:
        super().__init__()
        self.ingest_attempts = 0

    def contains(self, file_hash: str) -> bool:
        self.ingest_attempts += 1
        return super().contains(file_hash)


class _FlakyRetriever(FakeRetriever):
    def __init__(self) -> None:
        super().__init__()
        self.failures = 0
        self.add_attempts = 0

    def add(
        self, chunks: list[Chunk], vectors: list[list[float]], file_hash: str
    ) -> None:
        self.add_attempts += 1
        if self.failures:
            self.failures -= 1
            raise RetrievalError
        super().add(chunks, vectors, file_hash)


def _app_on(retriever: Retriever, plugin: Plugin | None = None) -> App:
    return assembled(
        chat_model=ScriptedChatModel([]), retriever=retriever, plugin=plugin
    )


def _page(app) -> None:
    from cora.frontends.streamlit.chat import render

    render(app)


def _main_page(app_factory) -> None:
    from cora.frontends.streamlit.chat import main

    main(app_factory)


def _run_main(app_factory) -> AppTest:
    at = AppTest.from_function(_main_page, args=(app_factory,))
    at.run()
    return at


def _run_page(app: App) -> AppTest:
    at = AppTest.from_function(_page, args=(app,))
    at.run()
    return at


def _visible_text(at: AppTest) -> str:
    return page_text(at)


def _sidebar_sources(at: AppTest) -> list[str]:
    return [md.value for md in at.sidebar.markdown]


def _memory_panel(at: AppTest):
    """The rail's fourth panel, where what cora remembers is listed and forgotten."""
    _plan, _source, _sessions, remembered = at.tabs
    return remembered


def _remembered(at: AppTest) -> list[str]:
    return [md.value for md in _memory_panel(at).markdown]


@pytest.mark.integration
def test_failed_turn_keeps_its_reason_across_a_rerun() -> None:
    at = _run_page(_app(FailingChatModel(LlmError())))

    at.chat_input[0].set_value("Hello?").run()
    at.run()

    assert not at.exception
    assert "Hello?" in _visible_text(at)
    assert [e.value for e in at.error] == [LlmError().user_message]
    assert at.chat_input


@dataclass(frozen=True)
class _RejectRule:
    phrase: str
    message: str

    def apply(self, user_input: str) -> None:
        if self.phrase in user_input:
            raise InputRejectedError(self.message)


@pytest.mark.integration
def test_thread_grows_past_a_failed_turn() -> None:
    refusal = "I can't advise on medication."
    answer = "BMI is weight over height squared."
    plugin = make_plugin(validation_rules=(_RejectRule("insulin", refusal),))
    at = _run_page(_app(ScriptedChatModel([ModelReply(text=answer)]), plugin=plugin))

    at.chat_input[0].set_value("Should I take insulin?").run()
    at.chat_input[0].set_value("What is BMI?").run()

    assert not at.exception
    text = _visible_text(at)
    assert "Should I take insulin?" in text
    assert "What is BMI?" in text
    assert answer in text
    assert [e.value for e in at.error] == [refusal]


@pytest.mark.integration
def test_second_question_carries_the_first_exchange_exactly_once() -> None:
    model = ScriptedChatModel([ModelReply(text="Noted."), ModelReply(text="80 kg.")])
    at = _run_page(_app(model))

    at.chat_input[0].set_value("I weigh 80 kg.").run()
    at.chat_input[0].set_value("What did I say my weight was?").run()

    assert not at.exception
    assert model.last_messages is not None
    assert [(m.role, m.content) for m in model.last_messages[1:]] == [
        ("user", "I weigh 80 kg."),
        ("assistant", "Noted."),
        ("user", "What did I say my weight was?"),
    ]


@pytest.mark.integration
def test_a_rejected_question_never_reaches_the_model_afterwards() -> None:
    refusal = "I can't advise on medication."
    plugin = make_plugin(validation_rules=(_RejectRule("insulin", refusal),))
    model = ScriptedChatModel([ModelReply(text="ok")])
    at = _run_page(_app(model, plugin=plugin))

    at.chat_input[0].set_value("Should I take insulin?").run()
    at.chat_input[0].set_value("What is BMI?").run()

    assert not at.exception
    assert model.last_messages is not None
    assert [(m.role, m.content) for m in model.last_messages[1:]] == [
        ("user", "What is BMI?"),
    ]


@pytest.mark.integration
def test_a_failure_carrying_no_message_still_renders_as_an_error() -> None:
    plugin = make_plugin(validation_rules=(_RejectRule("insulin", ""),))
    at = _run_page(_app(ScriptedChatModel([]), plugin=plugin))

    at.chat_input[0].set_value("Should I take insulin?").run()

    assert not at.exception
    assert len(at.error) == 1


@pytest.mark.integration
def test_upload_failure_shows_friendly_error_and_keeps_the_chat() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    at.file_uploader[0].set_value(("empty.txt", b"", "text/plain"))
    at.run()

    assert not at.exception
    expected = EmptyDocumentError("empty.txt").user_message
    assert [e.value for e in at.error] == [expected]
    assert at.chat_input


@pytest.mark.integration
def test_successful_upload_confirms_with_its_chunk_count() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()

    assert not at.exception
    [confirmation] = at.success
    assert "note.md" in confirmation.value
    assert "1 chunk" in confirmation.value


@pytest.mark.integration
def test_uploading_content_already_indexed_reports_a_duplicate() -> None:
    at = _run_page(indexed(_app(ScriptedChatModel([])), ("seed.md", b"protein facts")))

    at.file_uploader[0].set_value(("copy.md", b"protein facts", "text/markdown"))
    at.run()

    assert not at.exception
    assert not at.success
    [notice] = at.info
    assert "copy.md" in notice.value


@pytest.mark.integration
def test_a_new_selection_of_known_bytes_reports_the_duplicate() -> None:
    at = _run_page(_app(ScriptedChatModel([])))
    content = b"protein facts"

    at.file_uploader[0].set_value(("a.md", content, "text/markdown"))
    at.run()
    at.file_uploader[0].set_value(("b.md", content, "text/markdown"))
    at.run()

    assert not at.exception
    assert not at.success
    [notice] = at.info
    assert "b.md" in notice.value


@pytest.mark.integration
def test_a_transient_ingest_failure_is_retried_on_the_next_rerun() -> None:
    retriever = _FlakyRetriever()
    at = _run_page(_app_on(retriever))
    retriever.failures = 1

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    assert [e.value for e in at.error] == [RetrievalError().user_message]

    at.run()

    assert not at.exception
    assert not at.error
    [confirmation] = at.success
    assert "note.md" in confirmation.value


@pytest.mark.integration
def test_a_persistent_ingest_failure_stops_retrying() -> None:
    retriever = _FlakyRetriever()
    at = _run_page(_app_on(retriever))
    retriever.failures = 99

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    at.run()
    at.run()
    at.run()

    assert not at.exception
    assert retriever.add_attempts == 2


@pytest.mark.integration
def test_switching_files_mid_outage_gives_the_new_one_a_full_budget() -> None:
    retriever = _FlakyRetriever()
    at = _run_page(_app_on(retriever))
    retriever.failures = 99

    at.file_uploader[0].set_value(("a.md", b"first", "text/markdown"))
    at.run()
    assert retriever.add_attempts == 1  # a.md has spent one of its two

    at.file_uploader[0].set_value(("b.md", b"second", "text/markdown"))
    at.run()
    at.run()

    assert not at.exception
    assert retriever.add_attempts == 3


@pytest.mark.integration
def test_detaching_a_file_restores_its_attempt_budget() -> None:
    retriever = _FlakyRetriever()
    at = _run_page(_app_on(retriever))
    retriever.failures = 99
    upload = ("a.md", b"first", "text/markdown")

    at.file_uploader[0].set_value(upload)
    at.run()
    at.file_uploader[0].clear()
    at.run()
    at.file_uploader[0].set_value(upload)
    at.run()
    at.run()

    assert not at.exception
    assert retriever.add_attempts == 3


@pytest.mark.integration
def test_upload_error_clears_on_the_next_rerun_without_re_ingesting() -> None:
    retriever = _CountingRetriever()
    at = _run_page(indexed(_app_on(retriever), ("seed.md", b"protein facts")))
    retriever.ingest_attempts = 0

    at.file_uploader[0].set_value(("empty.txt", b"", "text/plain"))
    at.run()
    assert [e.value for e in at.error] == [EmptyDocumentError("empty.txt").user_message]

    at.run()

    assert not at.exception
    assert not at.error
    assert retriever.ingest_attempts == 1
    assert _sidebar_sources(at) == ["seed.md"]


@pytest.mark.integration
def test_detaching_a_file_lets_the_same_bytes_be_selected_again() -> None:
    retriever = _CountingRetriever()
    at = _run_page(_app_on(retriever))
    upload = ("note.md", b"protein facts", "text/markdown")

    at.file_uploader[0].set_value(upload)
    at.run()
    at.file_uploader[0].clear()
    at.run()
    at.file_uploader[0].set_value(upload)
    at.run()

    assert not at.exception
    assert retriever.ingest_attempts == 2
    [notice] = at.info
    assert "already in your knowledge base" in notice.value


@pytest.mark.integration
def test_main_renders_the_page_from_the_factory() -> None:
    at = _run_main(lambda: _app(ScriptedChatModel([ModelReply(text="hi")])))

    assert not at.exception
    assert at.chat_input


@pytest.mark.integration
def test_main_without_config_shows_friendly_error_and_no_chat() -> None:
    def broken_factory() -> App:
        raise ConfigurationError("OPENROUTER_API_KEY is not set.")

    at = _run_main(broken_factory)

    assert not at.exception
    assert [e.value for e in at.error] == ["OPENROUTER_API_KEY is not set."]
    assert not at.chat_input


@pytest.mark.integration
def test_main_shows_friendly_error_for_any_startup_core_error() -> None:
    def broken_factory() -> App:
        raise PluginLoadError("cora.plugins.nutriton", "module not found")

    at = _run_main(broken_factory)

    assert not at.exception
    expected = PluginLoadError("cora.plugins.nutriton", "module not found")
    assert [e.value for e in at.error] == [expected.user_message]
    assert not at.chat_input


def _calculating() -> ScriptedChatModel:
    call = ToolCall(name="add", arguments={"a": 17, "b": 25}, call_id="c1")
    return ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="Sum computed.")]
    )


def _traced(at: AppTest) -> str:
    """The trace reads as its summary lines plus the evidence under them, which
    is rendered as code rather than markdown so a document cannot forge a line."""
    [trace] = at.status
    written = [*(md.value for md in trace.markdown), *(c.value for c in trace.code)]
    return "\n".join([trace.label, *written])


@pytest.mark.integration
def test_the_trace_names_the_tool_its_arguments_and_what_came_back() -> None:
    at = _run_page(_app(_calculating(), plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    assert not at.exception
    assert "Sum computed." in _visible_text(at)
    assert "How I got there" in _traced(at)
    assert "add(a=17, b=25) → 42" in _traced(at)


@pytest.mark.integration
def test_the_answer_no_longer_prints_the_raw_payload_beside_itself() -> None:
    at = _run_page(_app(_calculating(), plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    assert "42" not in _visible_text(at), "the payload belongs in the trace only"
    assert "42" in _traced(at)
    assert [e.label for e in at.expander] == []


@pytest.mark.integration
def test_a_trace_survives_the_next_question() -> None:
    call = ToolCall(name="add", arguments={"a": 1, "b": 2}, call_id="c1")
    scripted = ScriptedChatModel(
        [
            ModelReply(tool_calls=(call,)),
            ModelReply(text="Three."),
            ModelReply(text="Hello!"),
        ]
    )
    at = _run_page(_app(scripted, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("1 + 2?").run()
    at.chat_input[0].set_value("Hi!").run()

    assert not at.exception
    first, second = at.status
    assert "add(a=1, b=2) → 3" in "\n".join(c.value for c in first.code)
    assert "Decided no tool was needed" in "\n".join(c.value for c in second.code)


@pytest.mark.integration
def test_a_greeting_is_traced_as_the_decision_not_to_use_a_tool() -> None:
    at = _run_page(_app(ScriptedChatModel([ModelReply(text="Hello!")])))

    at.chat_input[0].set_value("Hi!").run()

    assert not at.exception
    assert "Decided no tool was needed" in _traced(at)


@pytest.mark.integration
def test_a_turn_that_went_wrong_does_not_read_as_a_clean_one() -> None:
    """The warning is inside a collapsed panel, so the panel itself has to say
    the run degraded — otherwise nothing above the fold does."""
    call = ToolCall(name="add", arguments={"a": "one"}, call_id="c1")
    scripted = ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="I could not add those.")]
    )
    at = _run_page(_app(scripted, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("one + 25?").run()

    [trace] = at.status
    assert trace.state == "error"


@pytest.mark.integration
def test_a_turn_that_went_well_reads_as_a_clean_one() -> None:
    at = _run_page(_app(_calculating(), plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    [trace] = at.status
    assert trace.state == "complete"


@pytest.mark.integration
def test_a_failed_tool_is_traced_as_failed_and_the_answer_still_arrives() -> None:
    call = ToolCall(name="add", arguments={"a": "one"}, call_id="c1")
    scripted = ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="I could not add those.")]
    )
    at = _run_page(_app(scripted, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("one + 25?").run()

    assert not at.exception
    assert "I could not add those." in _visible_text(at)
    assert "invalid arguments" in _traced(at)


class _FailsOnTheSecondRound:
    def __init__(self, call: ToolCall) -> None:
        self.call = call
        self.completions = 0

    def complete(self, messages, tools, on_text=unheard) -> ModelReply:
        self.completions += 1
        if self.completions > 1:
            raise LlmError
        return ModelReply(tool_calls=(self.call,))


@pytest.mark.integration
def test_a_failed_run_keeps_the_steps_it_had_taken() -> None:
    call = ToolCall(name="add", arguments={"a": 17, "b": 25}, call_id="c1")
    model = _FailsOnTheSecondRound(call)
    at = _run_page(_app(model, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()
    at.run()

    assert [e.value for e in at.error] == [LlmError().user_message]
    assert "add(a=17, b=25) → 42" in _traced(at)


@pytest.mark.integration
def test_upload_then_ask_shows_an_answer_that_cites_the_document() -> None:
    answer = "Protein supports muscle growth [1]."
    searching = ModelReply(
        tool_calls=(
            ToolCall(
                name=SEARCH_TOOL_NAME, arguments={"query": "protein"}, call_id="call-1"
            ),
        )
    )
    at = _run_page(_app(ScriptedChatModel([searching, ModelReply(text=answer)])))
    assert not at.exception

    at.file_uploader[0].set_value(("note.md", b"protein facts", "text/markdown"))
    at.run()
    assert not at.exception
    assert "note.md" in _visible_text(at)

    at.chat_input[0].set_value("What about protein?").run()
    assert not at.exception
    assert answer in _visible_text(at)
    listed = [md.value for md in at.markdown if re.match(r"^\[\d+\] ", md.value)]
    assert listed == [], "the number in the answer is the way in, not a panel under it"
    assert "[1] note.md: protein facts" in _traced(at)
    assert "untrusted" not in _visible_text(at).lower(), (
        "the model's framing of the passages must not reach the user"
    )


def _remembering_app(memory) -> App:
    return assembled(memory=memory)


@pytest.mark.integration
def test_the_sidebar_lists_every_remembered_fact() -> None:
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))

    at = _run_page(_remembering_app(memory))

    listed = _remembered(at)
    assert "trains on Tuesdays" in listed
    assert "is vegetarian" in listed


@pytest.mark.integration
def test_a_fact_remembered_this_turn_is_listed_without_a_second_interaction() -> None:
    """The panel is drawn by the same run that answers, so what the turn remembered has
    to reach it: a user told "noted" who reads "nothing yet" beside it reads the store
    as broken, and clicking something else is not an answer."""
    memory = FakeMemory()
    remembering = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=REMEMBER_TOOL_NAME,
                        arguments={"fact": "is vegetarian"},
                        call_id="call-1",
                    ),
                )
            ),
            ModelReply(text="Noted."),
        ]
    )
    at = _run_page(assembled(chat_model=remembering, memory=memory))

    at.chat_input[0].set_value("Remember that I'm vegetarian.").run()

    assert not at.exception
    assert [fact.text for fact in memory.recall()] == ["is vegetarian"]
    assert "is vegetarian" in _remembered(at)


@pytest.mark.integration
def test_a_facts_own_button_forgets_just_that_fact() -> None:
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))
    doomed = memory.recall()[0]
    at = _run_page(_remembering_app(memory))

    _memory_panel(at).button(key=f"forget_{doomed.key}").click().run()

    assert [fact.text for fact in memory.recall()] == ["is vegetarian"]
    assert "trains on Tuesdays" not in _remembered(at)


@pytest.mark.integration
def test_clearing_empties_the_panel_and_a_rerun_keeps_it_empty() -> None:
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))
    at = _run_page(_remembering_app(memory))

    _memory_panel(at).button(key="clear_memory").click().run()

    assert memory.recall() == ()
    assert NOTHING_REMEMBERED in _remembered(at) + [c.value for c in at.caption]

    at.run()

    assert memory.recall() == ()


@pytest.mark.integration
def test_a_memory_that_cannot_be_reached_says_so_and_leaves_the_chat_alone() -> None:
    """The panel is a panel, not the app: a broken store must not take the chat down
    with it, and what it has to say belongs where it would have listed the facts."""
    at = _run_page(_remembering_app(FailingMemory(MemoryStoreError())))

    assert not at.exception
    assert [error.value for error in _memory_panel(at).error] == [
        MemoryStoreError().user_message
    ]
    assert at.chat_input


@pytest.mark.integration
def test_an_app_without_a_memory_shows_no_panel() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    assert REMEMBER_HEADING not in _remembered(at)


@pytest.mark.integration
@pytest.mark.parametrize("button", ["clear_memory", "forget"])
def test_a_write_that_cannot_reach_the_store_says_so_and_keeps_the_chat(
    button: str,
) -> None:
    """The panel is a sidebar, not the app — and the buttons are the half of it that a
    broken store reaches while they are already on screen."""
    memory = ReadOnlyMemory(("trains on Tuesdays",))
    at = _run_page(_remembering_app(memory))
    key = button if button == "clear_memory" else f"forget_{memory.recall()[0].key}"

    _memory_panel(at).button(key=key).click().run()

    assert not at.exception
    assert MemoryStoreError().user_message in [e.value for e in at.error]
    assert at.chat_input
    assert "trains on Tuesdays" in _remembered(at)


@pytest.mark.integration
def test_the_page_splits_into_a_conversation_and_a_rail() -> None:
    """The mockup's middle and right: what was said, and what it rests on. The
    conversation is the wider of the two — the rail annotates it, not the other way
    round."""
    at = _run_page(_app(ScriptedChatModel([])))

    conversation, rail = at.columns[:2]

    assert conversation.proto.weight > rail.proto.weight


@pytest.mark.integration
def test_the_question_is_asked_inside_the_conversation() -> None:
    """Pinned across the foot of the page, the input spanned the rail as well as the
    conversation it belongs to."""
    at = _run_page(_app(ScriptedChatModel([])))

    conversation, _rail = at.columns[:2]

    assert conversation.chat_input, "the question belongs to the conversation's column"


@pytest.mark.integration
def test_the_page_is_headed_by_the_app_and_what_it_is() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    assert [heading.value for heading in at.title] == [APP_NAME]
    assert TAGLINE in [caption.value for caption in at.caption]


def _said_in(panel) -> str:
    """Everything one panel of the rail says, whichever element says it."""
    return "\n".join(
        [
            *(element.value for element in panel.markdown),
            *(element.value for element in panel.code),
        ]
    )


@pytest.mark.integration
def test_the_rail_carries_four_panels() -> None:
    at = _run_page(_app(ScriptedChatModel([])))

    assert [panel.label for panel in at.tabs] == list(RAIL_PANELS)


@pytest.mark.integration
def test_the_plan_of_a_turn_is_in_the_rail_not_under_its_answer() -> None:
    """How the answer was reached is what the rail is for. Under the answer it was a
    panel per message, pushing the next question further down every turn."""
    at = _run_page(_app(_calculating(), plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    assert not at.exception
    plan, _source, _sessions, _memory = at.tabs
    assert "add(a=17, b=25) → 42" in _said_in(plan)
    conversation, _rail = at.columns[:2]
    assert not conversation.status, "the plan left the answer it sat under"


@pytest.mark.integration
def test_a_turn_that_went_wrong_says_so_in_the_rail() -> None:
    """A failed step sits inside a collapsed panel, and that panel now lives in the
    rail: if the news of a bad run did not travel with it, nothing on the page would
    carry it."""
    call = ToolCall(name="add", arguments={"a": "one"}, call_id="c1")
    scripted = ScriptedChatModel(
        [ModelReply(tool_calls=(call,)), ModelReply(text="I could not add those.")]
    )
    at = _run_page(_app(scripted, plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("one + 25?").run()

    plan, _source, _sessions, _memory = at.tabs
    [trace] = plan.status

    assert trace.state == "error"


def _holds(container, kind: str) -> bool:
    """Whether one part of the page holds a node of a given kind, at any depth. Read off
    the tree because the slot a turn streams into is cleared before the run ends: what
    survives is where it was drawn, not what it said."""
    pending = [container]
    while pending:
        node = pending.pop()
        if getattr(node, "type", None) == kind:
            return True
        children = getattr(node, "children", None)
        pending.extend(
            children.values() if isinstance(children, dict) else children or []
        )
    return False


@pytest.mark.integration
def test_the_steps_of_a_turn_in_progress_are_drawn_in_the_rail() -> None:
    """A turn streams its steps into a slot that is cleared once the answer lands, so
    the work in progress reads where the settled plan will: in the rail. Drawn in the
    conversation it pushed the answer down the page as the turn ran."""
    at = _run_page(_app(_calculating(), plugin=make_plugin(tools=(add_tool(),))))

    at.chat_input[0].set_value("17 + 25?").run()

    plan, _source, _sessions, _memory = at.tabs
    conversation, _rail = at.columns[:2]

    assert _holds(plan, "empty"), "the working slot belongs to the plan"
    assert not _holds(conversation, "empty"), "and not to the conversation"


@pytest.mark.integration
def test_the_memory_panel_is_in_the_rail_not_the_sidebar() -> None:
    """What cora has been told to remember is one of the four things the rail carries.
    The sidebar is left holding documents alone."""
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))

    at = _run_page(_remembering_app(memory))

    _plan, _source, _sessions, remembered = at.tabs
    assert "trains on Tuesdays" in _said_in(remembered)
    assert REMEMBER_HEADING not in _sidebar_sources(at)


@pytest.mark.integration
def test_a_fact_is_forgotten_from_the_panel_it_is_listed_in() -> None:
    memory = FakeMemory(("trains on Tuesdays", "is vegetarian"))
    doomed = memory.recall()[0]
    at = _run_page(_remembering_app(memory))

    _plan, _source, _sessions, remembered = at.tabs
    remembered.button(key=f"forget_{doomed.key}").click().run()

    assert [fact.text for fact in memory.recall()] == ["is vegetarian"]


@pytest.mark.integration
def test_the_rail_does_not_wait_for_an_answer_to_appear() -> None:
    """Drawn only once there was something to put in it, the rail would arrive with the
    first answer and shove the conversation sideways as the reader read it."""
    at = _run_page(_app(ScriptedChatModel([ModelReply(text="Hello!")])))
    unanswered = [panel.label for panel in at.tabs]

    at.chat_input[0].set_value("Hi!").run()

    assert unanswered == list(RAIL_PANELS)
    assert [panel.label for panel in at.tabs] == unanswered


def _sessions_panel(at: AppTest):
    _plan, _source, sessions, _memory = at.tabs
    return sessions


def _conversation_with(*recorded: tuple[str, str, str]) -> FakeConversations:
    conversations = FakeConversations()
    for thread, question, answer in recorded:
        conversations.record(
            thread, Turn(question=question, result=ChatResult(answer=answer))
        )
    return conversations


@pytest.mark.integration
def test_the_sessions_panel_lists_the_stored_conversations_newest_first() -> None:
    """A conversation is picked out of the list by what it was about; the thread id it
    is filed under says nothing to a reader."""
    conversations = _conversation_with(
        ("older", "How much protein?", "1.6 g per kg"),
        ("newer", "And creatine?", "Five grams."),
    )

    at = _run_page(
        assembled(chat_model=ScriptedChatModel([]), conversations=conversations)
    )

    assert [button.label for button in _sessions_panel(at).button] == [
        "And creatine?",
        "How much protein?",
    ]


@pytest.mark.integration
def test_the_conversation_in_progress_is_not_one_to_open() -> None:
    """You are already in it: offering to open it is an invitation to nothing, so the
    entry marks where the reader is instead."""
    conversations = _conversation_with(("older", "How much protein?", "1.6 g per kg"))
    at = _run_page(
        assembled(chat_model=ScriptedChatModel([]), conversations=conversations)
    )

    at.session_state.thread_id = "older"
    at.run()

    [entry] = _sessions_panel(at).button
    assert entry.disabled, "the conversation on screen is the one you cannot open"


@pytest.mark.integration
def test_opening_a_session_redraws_the_turns_it_holds() -> None:
    conversations = _conversation_with(("older", "How much protein?", "1.6 g per kg"))
    at = _run_page(
        assembled(chat_model=ScriptedChatModel([]), conversations=conversations)
    )

    _sessions_panel(at).button[0].click().run()

    assert not at.exception
    assert "1.6 g per kg" in _visible_text(at)


@pytest.mark.integration
def test_a_question_asked_after_opening_a_session_runs_on_that_thread() -> None:
    """Redrawing an old conversation and then answering into a new one is the failure
    this guards: the thread the agent is told about has to be the one on screen."""
    conversations = _conversation_with(("older", "How much protein?", "1.6 g per kg"))
    at = _run_page(
        assembled(
            chat_model=ScriptedChatModel([ModelReply(text="Five grams.")]),
            conversations=conversations,
        )
    )

    _sessions_panel(at).button[0].click().run()
    at.chat_input[0].set_value("And creatine?").run()

    assert not at.exception
    assert [turn.question for turn in conversations.turns("older")] == [
        "How much protein?",
        "And creatine?",
    ]


@pytest.mark.integration
def test_the_sessions_panel_says_what_will_fill_it_when_nothing_has() -> None:
    at = _run_page(
        assembled(chat_model=ScriptedChatModel([]), conversations=FakeConversations())
    )

    assert NO_SESSIONS in [line.value for line in _sessions_panel(at).caption]


@pytest.mark.integration
def test_a_conversation_store_that_cannot_be_read_costs_the_chat_nothing() -> None:
    """The panel is a panel, not the app: a store that went away takes the list of
    conversations with it and leaves the one on screen answering."""
    at = _run_page(
        assembled(
            chat_model=ScriptedChatModel([ModelReply(text="Five grams.")]),
            conversations=FailingConversations(),
        )
    )

    at.chat_input[0].set_value("And creatine?").run()

    assert not at.exception
    assert "Five grams." in _visible_text(at)
    assert [error.value for error in _sessions_panel(at).error] == [
        ConversationStoreError().user_message
    ]


@pytest.mark.integration
def test_a_session_that_cannot_be_opened_says_so_where_it_was_clicked() -> None:
    """Listing works and reading one fails: the failure belongs in the panel the click
    was in, and a rerun has to carry it there — a callback's error is gone otherwise."""
    conversations = _conversation_with(("older", "How much protein?", "1.6 g per kg"))
    at = _run_page(
        assembled(
            chat_model=ScriptedChatModel([]),
            conversations=UnopenableSessions(conversations),
        )
    )

    _sessions_panel(at).button[0].click().run()

    assert not at.exception
    assert [error.value for error in _sessions_panel(at).error] == [
        ConversationStoreError().user_message
    ]
