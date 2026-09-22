from collections.abc import Callable
from dataclasses import replace

import pytest

from cora.adapters.sqlite_vec_retriever import SqliteVecRetriever
from cora.domain.chunk import Chunk
from cora.domain.errors import RetrievalError
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeEmbedder


def test_the_index_round_trips_with_our_own_embeddings(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [
        make_chunk("alpha", index=0),
        make_chunk("beta", index=1),
        make_chunk("gamma", index=2),
    ]
    index.add(
        DEFAULT_SCOPE, chunks, embedder.embed([c.text for c in chunks]), file_hash="h"
    )

    [query_vector] = embedder.embed(["beta"])
    hits = index.query(DEFAULT_SCOPE, query_vector, k=2)

    assert len(hits) == 2
    assert hits[0].chunk == replace(
        chunks[1], text="", upload="h", scope=DEFAULT_SCOPE
    ), "a hit carries the span, the upload and the field it was added under"
    assert hits[0].score >= hits[1].score


def test_a_score_reads_nearest_first(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [make_chunk("alpha", index=0), make_chunk("something else", index=1)]
    index.add(
        DEFAULT_SCOPE, chunks, embedder.embed([c.text for c in chunks]), file_hash="h"
    )

    hits = index.query(DEFAULT_SCOPE, embedder.embed(["alpha"])[0], k=2)

    assert [hit.chunk.index for hit in hits] == [0, 1]
    assert hits[0].score > hits[1].score


def test_a_retrieved_passage_carries_its_span_and_no_text(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunk = make_chunk("a passage of some length", index=3, offset=120)
    index.add(DEFAULT_SCOPE, [chunk], embedder.embed([chunk.text]), file_hash="h")

    [hit] = index.query(DEFAULT_SCOPE, embedder.embed([chunk.text])[0], k=1)

    assert hit.chunk.text == ""
    assert (hit.chunk.offset, hit.chunk.length) == (120, len(chunk.text))
    assert hit.chunk.index == 3


def test_a_field_is_a_partition_of_its_own(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add(
        "travel",
        [make_chunk("kyoto", source="kyoto.md")],
        embedder.embed(["kyoto"]),
        "h1",
    )

    [query_vector] = embedder.embed(["kyoto"])

    assert index.query("fitness", query_vector, k=5) == []
    assert [hit.chunk.source for hit in index.query("travel", query_vector, k=5)] == [
        "kyoto.md"
    ]


def test_a_forgotten_upload_comes_back_from_no_query(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add(
        DEFAULT_SCOPE, [make_chunk("a", source="one.txt")], embedder.embed(["a"]), "h1"
    )
    index.add(
        DEFAULT_SCOPE, [make_chunk("b", source="two.txt")], embedder.embed(["b"]), "h2"
    )

    index.forget(DEFAULT_SCOPE, "h2")

    hits = index.query(DEFAULT_SCOPE, embedder.embed(["b"])[0], k=10)
    assert [hit.chunk.upload for hit in hits] == ["h1"]
    assert index.sources(DEFAULT_SCOPE) == ["one.txt"]
    assert not index.contains(DEFAULT_SCOPE, "h2")


def test_forgetting_one_upload_leaves_the_other_uploads_of_its_name(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add(
        DEFAULT_SCOPE, [make_chunk("a", source="one.txt")], embedder.embed(["a"]), "h1"
    )
    index.add(
        DEFAULT_SCOPE, [make_chunk("b", source="one.txt")], embedder.embed(["b"]), "h2"
    )

    index.forget(DEFAULT_SCOPE, "h1")

    assert index.contains(DEFAULT_SCOPE, "h2")
    assert index.sources(DEFAULT_SCOPE) == ["one.txt"]


def test_what_was_added_is_read_back_by_a_fresh_adapter_on_the_same_file(
    make_index: Callable[[], SqliteVecRetriever], make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunk = make_chunk("persisted")
    make_index().add(DEFAULT_SCOPE, [chunk], embedder.embed(["persisted"]), "h")

    hits = make_index().query(DEFAULT_SCOPE, embedder.embed(["persisted"])[0], k=1)

    assert len(hits) == 1
    assert hits[0].chunk == replace(chunk, text="", upload="h", scope=DEFAULT_SCOPE)


def test_re_adding_one_upload_leaves_one_copy_of_each_passage(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0), make_chunk("b", index=1)]
    vectors = embedder.embed([c.text for c in chunks])
    index.add(DEFAULT_SCOPE, chunks, vectors, file_hash="h")
    index.add(DEFAULT_SCOPE, chunks, vectors, file_hash="h")

    hits = index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=10)

    assert len(hits) == 2
    assert index.uploads(DEFAULT_SCOPE, "doc.txt") == ["h"]


def test_a_store_error_surfaces_as_retrieval_error(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add(DEFAULT_SCOPE, [make_chunk("a")], embedder.embed(["a"]), "h")
    index.close()

    with pytest.raises(RetrievalError):
        index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=1)


def test_an_upload_that_fails_half_way_leaves_nothing_behind(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0), make_chunk("b", index=1)]
    wrong_width = [embedder.embed(["a"])[0], [0.1, 0.2, 0.3]]

    with pytest.raises(RetrievalError):
        index.add(DEFAULT_SCOPE, chunks, wrong_width, file_hash="h")

    assert not index.contains(DEFAULT_SCOPE, "h")
    assert index.sources(DEFAULT_SCOPE) == []
    assert index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=5) == []


def test_the_store_holds_its_journal_in_write_ahead_mode(
    index: SqliteVecRetriever,
) -> None:
    [(mode,)] = index._connection.execute("pragma journal_mode")

    assert mode == "wal"
