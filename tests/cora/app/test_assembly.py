import logging
from pathlib import Path

import pytest

from cora.adapters.port_logging import LoggingChatModel
from cora.app.assembly import App, assemble, build
from cora.app.config import Config
from cora.app.log_config import DEBUG_HANDLER_NAME
from cora.core.chunk import Chunk
from cora.core.errors import InputRejectedError
from cora.core.ports.chat_model import ModelReply
from cora.core.ports.plugin import Plugin
from cora.core.ports.retrieval import RetrievedChunk
from cora.core.services.chat_engine import ChatEngine
from cora.core.services.fusion_context_source import FusionContextSource
from cora.core.services.hybrid_context_source import HybridContextSource
from cora.core.services.plugin_registry import load_plugin
from cora.core.services.query_planner import QueryPlanner
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


class _FakeKeywordStore:
    def __init__(self) -> None:
        self.added: list[Chunk] = []

    def add(self, chunks: list[Chunk]) -> None:
        self.added.extend(chunks)

    def search(self, query: str, k: int) -> list[RetrievedChunk]:
        return []


def _assemble(
    plugin: Plugin,
    *,
    chat_model: ScriptedChatModel | None = None,
    retriever: FakeRetriever | None = None,
    debug: bool = False,
) -> App:
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        plugin=plugin,
        debug=debug,
    )


def _seed_doc() -> tuple[tuple[str, bytes], ...]:
    return (("note.md", b"protein builds muscle"),)


def test_assemble_returns_app_exposing_engine_and_knowledge_base() -> None:
    plugin = make_plugin(seed_docs=(("note.md", b"protein supports muscle growth"),))

    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="42")]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=plugin,
    )

    assert isinstance(app, App)
    assert app.engine.answer("What is the answer?").answer == "42"
    assert "note.md" in app.knowledge_base.list_sources()


def test_assemble_answers_a_happy_path_question() -> None:
    app = _assemble(
        make_plugin(), chat_model=ScriptedChatModel([ModelReply(text="42")])
    )

    result = app.engine.answer("What is the answer?")

    assert result.answer == "42"


def test_assemble_plain_mode_uses_the_knowledge_base_as_context_source() -> None:
    app = _assemble(make_plugin())

    assert app.engine.knowledge_base is app.knowledge_base


def test_assemble_advanced_mode_wraps_the_knowledge_base_in_fusion() -> None:
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(),
        retrieval="advanced",
        fusion_queries=3,
    )

    source = app.engine.knowledge_base
    assert isinstance(source, FusionContextSource)
    assert app.knowledge_base is not source
    planner = source.planner
    assert isinstance(planner, QueryPlanner)
    assert planner.num_queries == 3


def test_assemble_hybrid_mode_wraps_dense_and_keyword_in_a_hybrid_source() -> None:
    keyword = _FakeKeywordStore()
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(),
        retrieval="hybrid",
        keyword_index=keyword,
    )

    source = app.engine.knowledge_base
    assert isinstance(source, HybridContextSource)
    assert source.dense is app.knowledge_base
    assert source.keyword is keyword


def test_assemble_passes_history_turns_to_the_engine() -> None:
    app = assemble(
        chat_model=ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=FakeRetriever(),
        plugin=make_plugin(),
        history_turns=6,
    )

    assert app.engine.max_history_turns == 6


def test_assemble_seeds_plugin_docs_into_the_knowledge_base() -> None:
    plugin = make_plugin(seed_docs=(("note.md", b"protein supports muscle growth"),))
    retriever = FakeRetriever()

    _assemble(plugin, retriever=retriever)

    assert "note.md" in retriever.sources()


class _RejectBanned:
    def apply(self, user_input: str) -> None:
        if "banned" in user_input:
            raise InputRejectedError("No banned words, please.")


def test_assemble_chains_core_and_plugin_validation_rules() -> None:
    app = _assemble(make_plugin(validation_rules=(_RejectBanned(),)))

    with pytest.raises(InputRejectedError):
        app.engine.answer("   ")  # core rule: empty input

    with pytest.raises(InputRejectedError):
        app.engine.answer("a banned word")  # plugin rule


def test_assemble_with_debug_logs_every_port_of_a_chat_turn(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = _assemble(make_plugin(seed_docs=_seed_doc()), debug=True)

    with caplog.at_level(logging.DEBUG, logger="cora"):
        app.engine.answer("How much protein?")

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "chat request" in logged
    assert "retrieval" in logged
    assert "embedding" in logged


def test_assemble_keeps_a_chat_turn_silent_without_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = _assemble(make_plugin(seed_docs=_seed_doc()))

    with caplog.at_level(logging.DEBUG, logger="cora"):
        app.engine.answer("How much protein?")

    assert caplog.records == []


def _config(db_path: Path, *, debug: bool = False) -> Config:
    return Config(
        api_key="k",
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        plugin_module="fixture_plugins.valid",
        top_k=3,
        max_tool_rounds=4,
        history_turns=6,
        db_path=str(db_path),
        debug=debug,
    )


@pytest.mark.integration
def test_build_wires_the_debug_seam_when_config_asks_for_it(
    tmp_path: Path, clean_cora_logger: logging.Logger
) -> None:
    app = build(_config(tmp_path, debug=True))

    assert isinstance(app.engine.chat_model, LoggingChatModel)
    assert clean_cora_logger.level == logging.DEBUG
    handlers = clean_cora_logger.handlers
    assert [handler.name for handler in handlers] == [DEBUG_HANDLER_NAME]


@pytest.mark.integration
def test_build_leaves_the_ports_bare_without_debug(
    tmp_path: Path, clean_cora_logger: logging.Logger
) -> None:
    app = build(_config(tmp_path))

    assert not isinstance(app.engine.chat_model, LoggingChatModel)
    assert clean_cora_logger.handlers == []


@pytest.mark.integration
def test_build_wires_real_adapters_from_config(tmp_path: Path) -> None:
    app = build(_config(tmp_path))

    plugin = load_plugin("fixture_plugins.valid")
    assert isinstance(app, App)
    assert app.knowledge_base is app.engine.knowledge_base
    engine = app.engine
    assert isinstance(engine, ChatEngine)
    assert engine.system_prompt == plugin.system_prompt
    assert engine.tools == plugin.tools
    assert engine.top_k == 3
    assert engine.max_tool_rounds == 4
    assert engine.max_history_turns == 6
    assert any(tmp_path.iterdir()), "the store must land under the configured path"
