import sqlite3
from pathlib import Path

import pytest

from cora.adapters.sqlite_documents import SqliteDocuments
from cora.domain.errors import DocumentStoreError

TEXT = "For strength training, aim for 1.6 g of protein per kg."


def _store(tmp_path: Path, name: str = "documents.sqlite") -> SqliteDocuments:
    return SqliteDocuments.at(str(tmp_path / name))


def test_what_was_kept_reads_back_unchanged(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.keep("protein.md", TEXT)

    assert store.read("protein.md") == TEXT


def test_a_document_survives_the_database_being_reopened(tmp_path: Path) -> None:
    """The pane opens a passage of a document uploaded in an earlier session, so the
    text has to outlive the process that ingested it."""
    first = _store(tmp_path)
    first.keep("protein.md", TEXT)
    first.close()

    assert _store(tmp_path).read("protein.md") == TEXT


def test_a_name_never_kept_reads_as_nothing(tmp_path: Path) -> None:
    assert _store(tmp_path).read("missing.md") is None


def test_keeping_one_name_twice_leaves_the_later_text(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.keep("protein.md", "first")
    store.keep("protein.md", "second")

    assert store.read("protein.md") == "second"


def test_a_driver_failure_surfaces_as_a_core_error(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.close()

    with pytest.raises(DocumentStoreError):
        store.keep("protein.md", TEXT)

    with pytest.raises(DocumentStoreError):
        store.read("protein.md")


def test_a_missing_parent_directory_is_created(tmp_path: Path) -> None:
    store = SqliteDocuments.at(str(tmp_path / "nested" / "deeper" / "documents.sqlite"))

    store.keep("protein.md", TEXT)

    assert (tmp_path / "nested" / "deeper" / "documents.sqlite").exists()


def test_the_text_is_stored_as_text_not_as_a_blob(tmp_path: Path) -> None:
    """Read back through the driver rather than through the adapter: an offset into a
    document is a character offset, so a store that round-tripped bytes would put the
    pane's highlight in the wrong place on any document with an umlaut in it."""
    path = tmp_path / "documents.sqlite"
    store = SqliteDocuments.at(str(path))
    store.keep("umlaut.md", "Müsli und Öl")
    store.close()

    with sqlite3.connect(path) as connection:
        [(kept,)] = connection.execute("select text from documents").fetchall()

    assert kept == "Müsli und Öl"
