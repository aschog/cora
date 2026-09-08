import sqlite3
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

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


def test_an_index_nothing_was_added_to_returns_nothing_at_all(
    index: SqliteVecRetriever,
) -> None:
    """The search tool reads an empty result as "you have uploaded nothing" and tells
    the model so. Nothing is written yet, so there is no vector table to search — that
    has to read as an empty field rather than a missing one."""
    [query_vector] = FakeEmbedder().embed(["anything at all"])

    assert index.query(DEFAULT_SCOPE, query_vector, k=5) == []


def test_the_vector_table_takes_its_width_from_the_vector_it_is_handed(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """How wide an embedding is belongs to the embedder, so a narrower one round-trips
    without the adapter being told."""
    narrow = FakeEmbedder(dim=5)
    index.add(DEFAULT_SCOPE, [make_chunk("a")], narrow.embed(["a"]), file_hash="h")

    hits = index.query(DEFAULT_SCOPE, narrow.embed(["a"])[0], k=1)

    assert [hit.chunk.upload for hit in hits] == ["h"]


def test_asking_for_more_neighbours_than_exist_returns_the_ones_that_do(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0), make_chunk("b", index=1)]
    index.add(DEFAULT_SCOPE, chunks, embedder.embed(["a", "b"]), file_hash="h")

    hits = index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=10)

    assert len(hits) == 2


def test_a_score_reads_nearest_first_within_nought_to_one(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """Cosine keeps the distance in nought to one, which is what makes one subtraction
    the score the port describes: higher is closer, and the merge across two fields
    sorts on it."""
    embedder = FakeEmbedder()
    chunks = [make_chunk("alpha", index=0), make_chunk("something else", index=1)]
    index.add(
        DEFAULT_SCOPE, chunks, embedder.embed([c.text for c in chunks]), file_hash="h"
    )

    hits = index.query(DEFAULT_SCOPE, embedder.embed(["alpha"])[0], k=2)

    assert [hit.chunk.index for hit in hits] == [0, 1]
    assert hits[0].score > hits[1].score
    assert all(0.0 <= hit.score <= 1.0 for hit in hits)


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
    """A field is unreachable from another rather than filtered out of it, so a leak is
    not one missing clause away."""
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


def test_an_empty_field_reads_as_empty_beside_a_field_that_holds_passages(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add("travel", [make_chunk("kyoto")], embedder.embed(["kyoto"]), "h1")

    assert index.sources("fitness") == []
    assert index.query("fitness", embedder.embed(["kyoto"])[0], k=5) == []


def test_sources_and_contains_read_only_the_field_they_were_asked_for(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    embedder = FakeEmbedder()
    index.add(
        "travel", [make_chunk("a", source="one.txt")], embedder.embed(["a"]), "h1"
    )
    index.add(
        "fitness", [make_chunk("b", source="two.txt")], embedder.embed(["b"]), "h2"
    )

    assert index.sources("travel") == ["one.txt"]
    assert index.sources("fitness") == ["two.txt"]
    assert index.contains("travel", "h1")
    assert not index.contains("travel", "h2")


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
    """The bytes name an upload, so one filename twice is two of them: forgetting the
    first must not take the second, whose passages are measured in its own text."""
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


def test_forgetting_an_upload_nothing_indexed_is_not_an_error(
    index: SqliteVecRetriever,
) -> None:
    index.forget(DEFAULT_SCOPE, "never-indexed")

    assert index.sources(DEFAULT_SCOPE) == []


def test_the_uploads_of_one_name_are_read_back_by_that_name(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """What the rail lists is a name, and what either store forgets is an upload: this
    is the mapping between them, and only the index holds it."""
    embedder = FakeEmbedder()
    index.add(
        DEFAULT_SCOPE,
        [
            make_chunk("a", source="one.txt", index=0),
            make_chunk("b", source="one.txt", index=1),
        ],
        embedder.embed(["a", "b"]),
        "h1",
    )
    index.add(
        DEFAULT_SCOPE, [make_chunk("c", source="one.txt")], embedder.embed(["c"]), "h2"
    )
    index.add(
        DEFAULT_SCOPE, [make_chunk("d", source="two.txt")], embedder.embed(["d"]), "h3"
    )

    assert index.uploads(DEFAULT_SCOPE, "one.txt") == ["h1", "h2"]
    assert index.uploads(DEFAULT_SCOPE, "two.txt") == ["h3"]


def test_a_name_nothing_was_uploaded_under_covers_no_uploads(
    index: SqliteVecRetriever,
) -> None:
    assert index.uploads(DEFAULT_SCOPE, "nothing.txt") == []


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
    """Ingesting the same bytes twice is the repair path, so the second write replaces
    what the first left rather than doubling it."""
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


def test_a_path_that_cannot_be_opened_surfaces_as_retrieval_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(RetrievalError):
        SqliteVecRetriever.at(str(tmp_path))


def test_a_build_that_refuses_extensions_surfaces_as_retrieval_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Python built without extension loading cannot hold the vectors at all, so it
    has to fail where the store is opened rather than at the first search."""

    def refuse(connection: sqlite3.Connection) -> None:
        raise sqlite3.OperationalError("extension loading is disabled")

    monkeypatch.setattr("cora.adapters.sqlite_vec_retriever.sqlite_vec.load", refuse)

    with pytest.raises(RetrievalError):
        SqliteVecRetriever.at(str(tmp_path / "index.sqlite"))


def test_a_written_passage_belongs_to_one_user(
    tmp_path: Path, make_chunk: Callable[..., Chunk]
) -> None:
    """The user is a column now so that a second one costs a value later: what this
    deployment writes is already invisible to anybody else on the same file."""
    embedder = FakeEmbedder()
    path = str(tmp_path / "index.sqlite")
    SqliteVecRetriever.at(path).add(
        DEFAULT_SCOPE, [make_chunk("a")], embedder.embed(["a"]), "h"
    )

    somebody_else = SqliteVecRetriever.at(path, user="another")

    assert SqliteVecRetriever.at(path).contains(DEFAULT_SCOPE, "h")
    assert somebody_else.sources(DEFAULT_SCOPE) == []
    assert not somebody_else.contains(DEFAULT_SCOPE, "h")
