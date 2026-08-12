import re
from dataclasses import dataclass

import pytest
from streamlit.testing.v1 import AppTest

from cora.app.assembly import App, assemble
from cora.domain.chunk import Chunk
from cora.domain.errors import (
    ConfigurationError,
    EmptyDocumentError,
    InputRejectedError,
    LlmError,
    PluginLoadError,
    RetrievalError,
)
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.plugin import Plugin, ToolCall
from cora.ports.retrieval import Retriever
from fakes import (
    FailingChatModel,
    FakeEmbedder,
    FakeRetriever,
    ScriptedChatModel,
    add_tool,
)
from fixture_plugins import make_plugin


def _app(chat_model: ChatModel, plugin: Plugin | None = None) -> App:
    return assemble(
        chat_model=chat_model,
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=plugin or make_plugin(),
    )


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
    return assemble(
        chat_model=ScriptedChatModel([]),
        embedder=FakeEmbedder(),
        retriever=retriever,
        plugin=plugin or make_plugin(),
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
    return "\n".join(md.value for md in at.markdown)


def _sidebar_sources(at: AppTest) -> list[str]:
    return [md.value for md in at.sidebar.markdown]


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
    plugin = make_plugin(seed_docs=(("seed.md", b"protein facts"),))
    at = _run_page(_app(ScriptedChatModel([]), plugin=plugin))

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
    plugin = make_plugin(seed_docs=(("seed.md", b"protein facts"),))
    at = _run_page(_app_on(retriever, plugin))
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

    def complete(self, messages, tools) -> ModelReply:
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
def test_upload_then_ask_shows_answer_with_sources() -> None:
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
    numbered = [md.value for md in at.markdown if re.match(r"^\[\d+\] ", md.value)]
    assert numbered == ["[1] note.md"]
    assert "[1] note.md: protein facts" in _traced(at)
    assert "untrusted" not in _visible_text(at).lower(), (
        "the model's framing of the passages must not reach the user"
    )
