import logging

import pytest

from cora.adapters.port_logging import (
    MAX_LOGGED_CHARS,
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
    truncate,
)
from cora.core.chunk import Chunk
from cora.core.ports.chat_model import Message, ModelReply
from cora.core.ports.plugin import ToolCall
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel, add_tool


def line_about(caplog: pytest.LogCaptureFixture, subject: str) -> str:
    matches = [r.getMessage() for r in caplog.records if subject in r.getMessage()]
    assert len(matches) == 1, f"expected one line about {subject!r}, got {matches}"
    return matches[0]


def test_truncate_passes_text_within_the_cap_through_unchanged() -> None:
    text = "short enough to log in full"

    assert truncate(text) == text


def test_truncate_bounds_long_text_and_marks_the_cut() -> None:
    clipped = truncate("x" * (MAX_LOGGED_CHARS * 3))

    assert len(clipped) <= MAX_LOGGED_CHARS
    assert clipped.endswith("…")


def test_logging_chat_model_delegates_and_returns_the_inner_reply() -> None:
    inner = ScriptedChatModel([ModelReply(text="an answer")])
    messages = (Message(role="user", content="a question"),)
    tools = (add_tool(),)

    reply = LoggingChatModel(inner).complete(messages, tools)

    assert reply == ModelReply(text="an answer")
    assert inner.last_messages == messages
    assert inner.last_tools == tools


def test_logging_chat_model_logs_the_request(caplog: pytest.LogCaptureFixture) -> None:
    inner = ScriptedChatModel([ModelReply(text="an answer")])
    messages = (
        Message(role="system", content="be helpful"),
        Message(role="user", content="a question"),
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(messages, ())

    request = line_about(caplog, "request")
    assert "2 messages" in request
    assert "system, user" in request
    assert "a question" in request
    assert all(record.name.startswith("cora") for record in caplog.records)
    assert {record.levelno for record in caplog.records} == {logging.DEBUG}


def test_logging_chat_model_logs_the_reply(caplog: pytest.LogCaptureFixture) -> None:
    inner = ScriptedChatModel(
        [
            ModelReply(
                text="here it comes: " + "filler " * MAX_LOGGED_CHARS + "TAIL",
                tool_calls=(ToolCall(name="add", arguments={"a": 1}, call_id="c1"),),
            )
        ]
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete((Message(role="user", content="hi"),), ())

    reply = line_about(caplog, "reply")
    assert "add" in reply
    assert "here it comes" in reply
    assert "TAIL" not in reply


def test_logging_chat_model_never_logs_a_buried_marker(
    caplog: pytest.LogCaptureFixture,
) -> None:
    buried = "filler " * MAX_LOGGED_CHARS + "BURIED"
    inner = ScriptedChatModel([ModelReply(text=buried)])
    messages = (
        Message(role="system", content=buried),
        Message(role="user", content=buried),
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(messages, ())

    logged = [record.getMessage() for record in caplog.records]
    assert len(logged) == 2
    assert not any("BURIED" in line for line in logged)


def test_logging_chat_model_bounds_the_roles_of_a_long_history(
    caplog: pytest.LogCaptureFixture,
) -> None:
    history = tuple(
        Message(role="user" if turn % 2 == 0 else "assistant", content="short")
        for turn in range(200)
    )
    inner = ScriptedChatModel([ModelReply(text="ok")])

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete(history, ())

    request = line_about(caplog, "request")
    assert "200 messages" in request
    assert len(request) <= 3 * MAX_LOGGED_CHARS


def test_logging_chat_model_bounds_hallucinated_tool_call_names(
    caplog: pytest.LogCaptureFixture,
) -> None:
    inner = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=tuple(
                    ToolCall(
                        name=f"tool_{turn}_" + "x" * MAX_LOGGED_CHARS,
                        arguments={},
                        call_id=f"c{turn}",
                    )
                    for turn in range(50)
                )
            )
        ]
    )

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingChatModel(inner).complete((Message(role="user", content="hi"),), ())

    assert len(line_about(caplog, "reply")) <= 3 * MAX_LOGGED_CHARS


def test_logging_retriever_delegates_and_logs_the_hits(
    caplog: pytest.LogCaptureFixture,
) -> None:
    embedder = FakeEmbedder()
    inner = FakeRetriever()
    chunk = Chunk(text="protein needs", source="guide.pdf", index=2, offset=40)
    inner.add([chunk], embedder.embed([chunk.text]), "hash-1")
    query_vector = embedder.embed([chunk.text])[0]

    with caplog.at_level(logging.DEBUG, logger="cora"):
        hits = LoggingRetriever(inner).query(query_vector, k=3)

    assert [hit.chunk for hit in hits] == [chunk]
    retrieval = line_about(caplog, "retrieval")
    assert "k=3" in retrieval
    assert "guide.pdf" in retrieval
    assert "1.00" in retrieval


def test_logging_retriever_delegates_and_logs_an_add(
    caplog: pytest.LogCaptureFixture,
) -> None:
    embedder = FakeEmbedder()
    inner = FakeRetriever()
    chunks = [
        Chunk(text=f"part {turn}", source="guide.pdf", index=turn, offset=turn * 10)
        for turn in range(3)
    ]
    vectors = embedder.embed([chunk.text for chunk in chunks])

    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingRetriever(inner).add(chunks, vectors, "hash-1")

    assert inner.sources() == ["guide.pdf"]
    assert inner.contains("hash-1")
    indexed = line_about(caplog, "indexed")
    assert "3 chunks" in indexed
    assert "guide.pdf" in indexed


def test_logging_retriever_survives_an_add_with_no_chunks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingRetriever(FakeRetriever()).add([], [], "hash-1")

    assert "0 chunks" in line_about(caplog, "indexed")


def test_logging_retriever_answers_lookups_silently(
    caplog: pytest.LogCaptureFixture,
) -> None:
    embedder = FakeEmbedder()
    inner = FakeRetriever()
    chunk = Chunk(text="protein needs", source="guide.pdf", index=0, offset=0)
    inner.add([chunk], embedder.embed([chunk.text]), "hash-1")
    retriever = LoggingRetriever(inner)

    with caplog.at_level(logging.DEBUG, logger="cora"):
        sources = retriever.sources()
        known = retriever.contains("hash-1")
        unknown = retriever.contains("hash-2")

    assert sources == ["guide.pdf"]
    assert known is True
    assert unknown is False
    assert caplog.records == []


def test_logging_embedder_delegates_and_logs_the_batch_size(
    caplog: pytest.LogCaptureFixture,
) -> None:
    inner = FakeEmbedder()
    texts = ["one", "two", "three"]

    with caplog.at_level(logging.DEBUG, logger="cora"):
        vectors = LoggingEmbedder(inner).embed(texts)

    assert vectors == inner.embed(texts)
    assert "3 texts" in line_about(caplog, "embedded")
