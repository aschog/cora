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


def test_a_score_reads_nearest_first(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """One subtraction from a cosine distance is the cosine similarity itself, which is
    the score the port describes: higher is closer, and the merge across two fields
    sorts on it. The range is minus one to one, so nothing may read an absolute value
    as a threshold."""
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


class _OmittingExtensions:
    """A connection from a build compiled with `SQLITE_OMIT_LOAD_EXTENSION`, where the
    method is absent rather than failing. Hand-written, because `sqlite3.Connection` is
    immutable and this is the one thing a real one on this machine cannot be."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __getattr__(self, name: str) -> object:
        if name == "enable_load_extension":
            raise AttributeError(name)
        return getattr(self.connection, name)


def test_a_build_without_the_call_at_all_surfaces_as_retrieval_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`SQLITE_OMIT_LOAD_EXTENSION` leaves the method off the connection rather than
    raising from it, so the failure arrives as an `AttributeError` and has to be caught
    as one — the same store, unreachable the same way."""
    connect = sqlite3.connect
    monkeypatch.setattr(
        "cora.adapters.sqlite_vec_retriever.sqlite3.connect",
        lambda *args, **kwargs: _OmittingExtensions(connect(":memory:")),
    )

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


def test_an_upload_that_fails_half_way_leaves_nothing_behind(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """The engine gates a re-upload on `contains`, so a passage written without its
    vector is a document the rail lists, the model cannot find, and re-uploading will
    not repair. One write, or none."""
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0), make_chunk("b", index=1)]
    wrong_width = [embedder.embed(["a"])[0], [0.1, 0.2, 0.3]]

    with pytest.raises(RetrievalError):
        index.add(DEFAULT_SCOPE, chunks, wrong_width, file_hash="h")

    assert not index.contains(DEFAULT_SCOPE, "h")
    assert index.sources(DEFAULT_SCOPE) == []
    assert index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=5) == []


def test_a_failed_re_index_leaves_the_copy_it_was_replacing(
    index: SqliteVecRetriever, make_chunk: Callable[..., Chunk]
) -> None:
    """Re-indexing clears the upload first, so a failure part-way through must not take
    the good copy with it."""
    embedder = FakeEmbedder()
    chunks = [make_chunk("a", index=0)]
    index.add(DEFAULT_SCOPE, chunks, embedder.embed(["a"]), file_hash="h")

    with pytest.raises(RetrievalError):
        index.add(DEFAULT_SCOPE, chunks, [[0.1, 0.2, 0.3]], file_hash="h")

    assert index.contains(DEFAULT_SCOPE, "h")
    assert [
        hit.chunk.upload
        for hit in index.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=5)
    ] == ["h"]


def test_a_query_reads_only_the_user_it_was_opened_for(
    tmp_path: Path, make_chunk: Callable[..., Chunk]
) -> None:
    """Searching is the one method that goes through the vector table, so it is the one
    that could hand back another user's passage without the join saying otherwise."""
    embedder = FakeEmbedder()
    path = str(tmp_path / "index.sqlite")
    SqliteVecRetriever.at(path).add(
        DEFAULT_SCOPE, [make_chunk("a", source="secret.md")], embedder.embed(["a"]), "h"
    )

    somebody_else = SqliteVecRetriever.at(path, user="another")

    assert somebody_else.query(DEFAULT_SCOPE, embedder.embed(["a"])[0], k=5) == []


def test_an_upload_of_no_chunks_writes_nothing(index: SqliteVecRetriever) -> None:
    """An empty document reaches the engine's own refusal, not a vector table made at
    the width of a vector that is not there."""
    index.add(DEFAULT_SCOPE, [], [], file_hash="h")

    assert not index.contains(DEFAULT_SCOPE, "h")


def test_the_store_holds_its_journal_in_write_ahead_mode(
    index: SqliteVecRetriever,
) -> None:
    """Four writers share this file, and the default journal takes an exclusive lock
    that blocks readers for the length of a write."""
    [(mode,)] = index._connection.execute("pragma journal_mode")

    assert mode == "wal"


def test_a_path_whose_directory_cannot_be_made_surfaces_as_retrieval_error(
    tmp_path: Path,
) -> None:
    """Making the directory is the first thing opening a store does, and it fails as an
    `OSError` rather than a database error — the port promises one error for a store it
    cannot reach, however far it got."""
    blocked = tmp_path / "a-file"
    blocked.write_text("not a directory")

    with pytest.raises(RetrievalError):
        SqliteVecRetriever.at(str(blocked / "cora.sqlite"))
