import logging
from dataclasses import replace

import pytest

from cora.domain.chunk import Chunk
from cora.domain.errors import EmbeddingError, LlmError, RetrievalError
from cora.engine.port_logging import (
    MAX_LOGGED_CHARS,
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
    truncate,
)
from cora.ports.chat_model import Message, ModelReply
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.plugin import ToolCall
from fakes import (
    FailingChatModel,
    FailingEmbedder,
    FailingRetriever,
    FakeEmbedder,
    FakeRetriever,
    ScriptedChatModel,
    add_tool,
)


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


def test_truncate_keeps_a_multi_line_value_on_one_line() -> None:
    collapsed = truncate("first\nsecond\r\nthird\tfourth")

    assert "\n" not in collapsed
    assert "\r" not in collapsed
    assert "\t" not in collapsed
    assert collapsed == "first second third fourth"


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


def test_logging_chat_model_reraises_the_inner_failure_unchanged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failure = LlmError()
    model = LoggingChatModel(FailingChatModel(failure))

    with (
        caplog.at_level(logging.DEBUG, logger="cora"),
        pytest.raises(LlmError) as raised,
    ):
        model.complete((Message(role="user", content="hi"),), ())

    assert raised.value is failure
    assert [record.getMessage() for record in caplog.records] == [
        line_about(caplog, "request")
    ]


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
    inner.add(DEFAULT_SCOPE, [chunk], embedder.embed([chunk.text]), "hash-1")
    query_vector = embedder.embed([chunk.text])[0]

    with caplog.at_level(logging.DEBUG, logger="cora"):
        hits = LoggingRetriever(inner).query(DEFAULT_SCOPE, query_vector, k=3)

    assert [hit.chunk for hit in hits] == [
        replace(chunk, upload="hash-1", scope=DEFAULT_SCOPE)
    ]
    retrieval = line_about(caplog, "retrieval")
    assert "k=3" in retrieval
    assert "guide.pdf" in retrieval
    assert "1.00" in retrieval
    assert "filter" not in retrieval
    assert {record.levelno for record in caplog.records} == {logging.DEBUG}


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
        LoggingRetriever(inner).add(DEFAULT_SCOPE, chunks, vectors, "hash-1")

    assert inner.sources(DEFAULT_SCOPE) == ["guide.pdf"]
    assert inner.contains(DEFAULT_SCOPE, "hash-1")
    indexed = line_about(caplog, "indexing")
    assert "3 chunks" in indexed
    assert "guide.pdf" in indexed


def test_logging_retriever_survives_an_add_with_no_chunks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG, logger="cora"):
        LoggingRetriever(FakeRetriever()).add(DEFAULT_SCOPE, [], [], "hash-1")

    assert "0 chunks" in line_about(caplog, "indexing")


def test_logging_retriever_announces_an_add_before_attempting_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    chunk = Chunk(text="text", source="guide.pdf", index=0, offset=0)

    with (
        caplog.at_level(logging.DEBUG, logger="cora"),
        pytest.raises(RetrievalError),
    ):
        LoggingRetriever(FailingRetriever(RetrievalError())).add(
            DEFAULT_SCOPE, [chunk], [[0.1]], "hash-1"
        )

    assert "1 chunks" in line_about(caplog, "indexing")


def test_logging_retriever_reraises_a_failed_query(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failure = RetrievalError()

    with (
        caplog.at_level(logging.DEBUG, logger="cora"),
        pytest.raises(RetrievalError) as raised,
    ):
        LoggingRetriever(FailingRetriever(failure)).query(DEFAULT_SCOPE, [0.1], k=3)

    assert raised.value is failure
    assert caplog.records == []


def test_logging_retriever_answers_lookups_silently(
    caplog: pytest.LogCaptureFixture,
) -> None:
    embedder = FakeEmbedder()
    inner = FakeRetriever()
    chunk = Chunk(text="protein needs", source="guide.pdf", index=0, offset=0)
    inner.add(DEFAULT_SCOPE, [chunk], embedder.embed([chunk.text]), "hash-1")
    retriever = LoggingRetriever(inner)

    with caplog.at_level(logging.DEBUG, logger="cora"):
        sources = retriever.sources(DEFAULT_SCOPE)
        known = retriever.contains(DEFAULT_SCOPE, "hash-1")
        unknown = retriever.contains(DEFAULT_SCOPE, "hash-2")

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
    assert "3 texts" in line_about(caplog, "embedding")
    assert {record.levelno for record in caplog.records} == {logging.DEBUG}


def test_logging_embedder_announces_a_batch_before_attempting_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failure = EmbeddingError()

    with (
        caplog.at_level(logging.DEBUG, logger="cora"),
        pytest.raises(EmbeddingError) as raised,
    ):
        LoggingEmbedder(FailingEmbedder(failure)).embed(["one", "two"])

    assert raised.value is failure
    assert "2 texts" in line_about(caplog, "embedding")
