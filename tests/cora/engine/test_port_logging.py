"""What `CORA_DEBUG` wraps, held to adding nothing.

Two properties, because the module makes two claims: that what is logged is bounded —
a page of prompt per turn is how a debug log stops being read — and that nothing about
a turn changes because someone is watching. The second is the one worth a test: a
wrapper that quietly dropped a hit would be a deployment answering differently with
debug on than with it off, and every other test in the suite runs with it off.
"""

from cora.domain.chunk import Chunk
from cora.engine.port_logging import (
    MAX_LOGGED_CHARS,
    LoggingChatModel,
    LoggingEmbedder,
    LoggingRetriever,
    truncate,
)
from cora.ports.chat_model import Message, ModelReply
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel, add_tool

QUESTION = (Message(role="user", content="a question"),)


def test_truncate_bounds_a_value_and_keeps_it_on_one_line() -> None:
    clipped = truncate("x" * (MAX_LOGGED_CHARS * 3))

    assert len(clipped) <= MAX_LOGGED_CHARS and clipped.endswith("…")
    assert truncate("first\nsecond\r\nthird\tfourth") == "first second third fourth"


def test_a_watched_model_answers_what_the_model_answered() -> None:
    reply = ModelReply(text="an answer")

    watched = LoggingChatModel(ScriptedChatModel([reply])).complete(QUESTION, ())

    assert watched == reply


def test_a_watched_index_reads_back_what_was_written_to_it() -> None:
    embedder, inner = FakeEmbedder(), FakeRetriever()
    chunks = [
        Chunk(text=f"passage {n}", source="note.md", index=n, offset=n * 10)
        for n in range(3)
    ]
    watched = LoggingRetriever(inner)

    watched.add(DEFAULT_SCOPE, chunks, embedder.embed([c.text for c in chunks]), "h")
    hits = watched.query(DEFAULT_SCOPE, embedder.embed(["passage 1"])[0], k=3)

    assert hits == inner.query(DEFAULT_SCOPE, embedder.embed(["passage 1"])[0], k=3)
    assert len(hits) == len(chunks), "every passage written is a passage read back"
    assert watched.sources(DEFAULT_SCOPE) == inner.sources(DEFAULT_SCOPE) == ["note.md"]
    assert watched.contains(DEFAULT_SCOPE, "h")
    assert watched.uploads(DEFAULT_SCOPE, "note.md") == ["h"]

    watched.forget(DEFAULT_SCOPE, "h")

    assert watched.sources(DEFAULT_SCOPE) == []


def test_a_watched_embedder_hands_back_the_vectors_it_was_given() -> None:
    inner = FakeEmbedder()

    assert LoggingEmbedder(inner).embed(["a", "b"]) == inner.embed(["a", "b"])


def test_watching_a_tool_round_leaves_the_round_as_it_was() -> None:
    """The wrapper is a dataclass over the port, so the tools it is handed reach the
    model it wraps — a round that lost them would answer without ever calling one."""
    inner = ScriptedChatModel([ModelReply(text="done")])

    LoggingChatModel(inner).complete(QUESTION, (add_tool(),))

    assert inner.last_tools == (add_tool(),)
    assert inner.last_messages == QUESTION
