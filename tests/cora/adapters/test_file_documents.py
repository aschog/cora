from pathlib import Path

import pytest

from cora.adapters.file_documents import FileDocuments
from cora.domain.errors import DocumentStoreError

TEXT = "For strength training, aim for 1.6 g of protein per kg."
OTHER = "The sleeper to Kyoto sells out a month before the maples turn."
UPLOAD = "7692c3ad3540bb803c020b3aee66cd8887123234ea0c6e7143c0add73ff431ed"
ANOTHER = "3fc4ccfe745870e2c0d99f71f30ff0656c8dedd41cc1d7d3d376b0dbe685e2f3"
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


def test_a_forgotten_upload_leaves_no_file_and_reads_as_nothing(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    store.keep(FITNESS, UPLOAD, "protein.md", TEXT)

    store.forget(FITNESS, UPLOAD)

    assert store.read(FITNESS, UPLOAD) is None
    assert list((tmp_path / FITNESS).glob("*.md")) == []


def test_forgetting_one_upload_leaves_the_other_files_where_they_are(
    tmp_path: Path,
) -> None:
    """One filename twice is two files, and each holds the text its own passages were
    measured in: forgetting one must not take the other."""
    store = _store(tmp_path)
    store.keep(FITNESS, UPLOAD, "protein.md", TEXT)
    store.keep(FITNESS, ANOTHER, "protein.md", OTHER)
    store.keep(TRAVEL, UPLOAD, "protein.md", TEXT)

    store.forget(FITNESS, UPLOAD)

    assert store.read(FITNESS, ANOTHER) == OTHER
    assert store.read(TRAVEL, UPLOAD) == TEXT


def test_forgetting_an_upload_no_file_was_kept_for_is_not_an_error(
    tmp_path: Path,
) -> None:
    """The index went first, so this store may be asked for a file that was never
    written — and being asked twice is the second ask already done."""
    store = _store(tmp_path)

    store.forget(FITNESS, UPLOAD)

    assert store.read(FITNESS, UPLOAD) is None


def test_a_scope_that_walks_out_of_the_root_forgets_nothing(tmp_path: Path) -> None:
    """The same guard `read` holds, on the way out: a field name reaches here from a
    request, and one that resolves outside the root must delete nothing."""
    root = tmp_path / "documents"
    store = FileDocuments.at(str(root))
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    kept = outside / f"secret-{UPLOAD[:12]}.md"
    kept.write_text("another field's text")

    store.forget("../elsewhere", UPLOAD)

    assert kept.exists()


def test_a_file_that_cannot_be_deleted_raises(tmp_path: Path) -> None:
    """The store says what happened rather than reporting a delete that did not: a
    directory nothing may be removed from is the failure this translates."""
    store = _store(tmp_path)
    store.keep(FITNESS, UPLOAD, "protein.md", TEXT)
    folder = tmp_path / FITNESS
    folder.chmod(0o500)
    try:
        with pytest.raises(DocumentStoreError):
            store.forget(FITNESS, UPLOAD)
    finally:
        folder.chmod(0o700)


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


def test_a_prefix_of_an_upload_does_not_read_it(tmp_path: Path) -> None:
    """The hash in the filename is short so the directory reads well, and short is not
    a name to accept from a URL: an upload is read by the whole of what it is."""
    store = _store(tmp_path)
    store.keep(FITNESS, UPLOAD, "notes.md", TEXT)

    assert store.read(FITNESS, UPLOAD[:12]) is None
    assert store.read(FITNESS, UPLOAD) == TEXT


def test_a_scope_that_walks_out_of_the_root_reads_nothing(tmp_path: Path) -> None:
    """A name no field has is a document this store does not hold, which is what `read`
    says with nothing. The file it would have walked to is put there first, or the guard
    is held by an empty directory rather than by itself."""
    root = tmp_path / "documents"
    store = FileDocuments.at(str(root))
    store.keep(FITNESS, UPLOAD, "notes.md", TEXT)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / f"secret-{UPLOAD[:12]}.md").write_text("another field's text")

    assert store.read("../elsewhere", UPLOAD) is None
    assert store.read("fitness/../../elsewhere", UPLOAD) is None
    assert store.read(FITNESS, UPLOAD) == TEXT


def test_an_upload_with_no_filename_is_still_a_file_that_can_be_read(
    tmp_path: Path,
) -> None:
    """A form can arrive naming no file at all, and a document kept under no name is
    still a citation waiting to be opened."""
    store = _store(tmp_path)

    store.keep(FITNESS, UPLOAD, "", TEXT)

    assert store.read(FITNESS, UPLOAD) == TEXT
