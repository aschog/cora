from pathlib import Path

import pytest

from cora.adapters.file_documents import FileDocuments
from cora.domain.errors import DocumentStoreError

TEXT = "For strength training, aim for 1.6 g of protein per kg."
OTHER = "The sleeper to Kyoto sells out a month before the maples turn."
UPLOAD = "3f786850e387550fdab836ed7e6dc881de23001b"
ANOTHER = "89e6c98d92887913cadf06b2adb97f26cde4849b"
FITNESS, TRAVEL = "fitness", "travel"


def _store(tmp_path: Path) -> FileDocuments:
    return FileDocuments.at(str(tmp_path))


def test_a_kept_document_is_one_markdown_file_under_its_field(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.keep(FITNESS, UPLOAD, "protein.md", TEXT)

    [written] = (tmp_path / FITNESS).glob("*.md")
    assert written.read_text() == TEXT
    assert written.name.startswith("protein")
    assert store.read(FITNESS, UPLOAD) == TEXT


def test_one_filename_uploaded_twice_is_two_files(tmp_path: Path) -> None:
    """The bytes name the upload, so a citation into the first still opens onto the
    text it was measured in after the second arrives."""
    store = _store(tmp_path)

    store.keep(FITNESS, UPLOAD, "notes.md", TEXT)
    store.keep(FITNESS, ANOTHER, "notes.md", OTHER)

    assert len(list((tmp_path / FITNESS).glob("*.md"))) == 2
    assert store.read(FITNESS, UPLOAD) == TEXT
    assert store.read(FITNESS, ANOTHER) == OTHER


def test_a_field_reads_only_its_own_documents(tmp_path: Path) -> None:
    store = _store(tmp_path)

    store.keep(FITNESS, UPLOAD, "notes.md", TEXT)
    store.keep(TRAVEL, UPLOAD, "notes.md", OTHER)

    assert store.read(FITNESS, UPLOAD) == TEXT
    assert store.read(TRAVEL, UPLOAD) == OTHER


def test_an_upload_never_kept_reads_as_nothing(tmp_path: Path) -> None:
    assert _store(tmp_path).read(FITNESS, UPLOAD) is None


def test_a_scope_that_is_not_a_bare_name_is_refused(tmp_path: Path) -> None:
    """The name reaches here from an upload, so a field that walks out of the root is
    refused before anything is written."""
    store = _store(tmp_path)

    with pytest.raises(DocumentStoreError):
        store.keep("../elsewhere", UPLOAD, "notes.md", TEXT)

    assert not list(tmp_path.parent.glob("elsewhere/*"))


def test_a_root_that_cannot_be_written_raises(tmp_path: Path) -> None:
    blocked = tmp_path / "root"
    blocked.write_text("not a directory")

    with pytest.raises(DocumentStoreError):
        FileDocuments.at(str(blocked)).keep(FITNESS, UPLOAD, "notes.md", TEXT)
