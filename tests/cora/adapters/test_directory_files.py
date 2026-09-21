from pathlib import Path

import pytest

from cora.adapters.directory_files import DirectoryFiles
from cora.domain.errors import (
    FieldFileError,
    FileNameRejectedError,
    FileTooLargeToKeepError,
)

LIST = "| Deutsch | English |\n| --- | --- |\n| Apfel | apple |\n"
OTHER = "| Deutsch | English |\n| --- | --- |\n| Hund | dog |\n"
VOCAB, NOTES = "vocab", "notes"
NAME = "Grundwortschatz.md"


def _files(tmp_path: Path, cap: int = 1_000_000) -> DirectoryFiles:
    return DirectoryFiles.at(str(tmp_path), cap)


def test_what_was_written_is_read_back_from_a_fresh_adapter(tmp_path: Path) -> None:
    _files(tmp_path).write(VOCAB, NAME, LIST)

    assert _files(tmp_path).read(VOCAB, NAME) == LIST


def test_one_name_in_two_fields_is_two_files(tmp_path: Path) -> None:
    files = _files(tmp_path)

    files.write(VOCAB, NAME, LIST)
    files.write(NOTES, NAME, OTHER)

    assert files.read(VOCAB, NAME) == LIST
    assert files.read(NOTES, NAME) == OTHER


def test_a_name_nothing_was_written_under_reads_as_nothing(tmp_path: Path) -> None:
    assert _files(tmp_path).read(VOCAB, "nothing.md") is None


def test_writing_nothing_drops_the_name_and_unlists_it(tmp_path: Path) -> None:
    files = _files(tmp_path)
    files.write(VOCAB, NAME, LIST)

    files.write(VOCAB, NAME, None)

    assert files.read(VOCAB, NAME) is None
    assert files.names(VOCAB) == ()


def test_dropping_a_name_nothing_was_written_under_is_not_an_error(
    tmp_path: Path,
) -> None:
    _files(tmp_path).write(VOCAB, "never.md", None)


def test_a_field_lists_its_own_names_sorted_and_no_others(tmp_path: Path) -> None:
    files = _files(tmp_path)
    files.write(VOCAB, "b.md", LIST)
    files.write(VOCAB, "a.md", LIST)
    files.write(NOTES, "elsewhere.md", OTHER)

    assert files.names(VOCAB) == ("a.md", "b.md")


def test_a_field_nothing_was_written_into_lists_nothing(tmp_path: Path) -> None:
    assert _files(tmp_path).names(VOCAB) == ()


# What a real directory also holds: the machine's own files, and a folder. A listing
# that returned one would hand back a name its own reader refuses, which is how one
# `.DS_Store` broke every tool in a field.
def test_only_names_this_store_could_have_written_are_listed(tmp_path: Path) -> None:
    files = _files(tmp_path)
    files.write(VOCAB, NAME, LIST)
    (tmp_path / VOCAB / ".DS_Store").write_bytes(b"junk")
    (tmp_path / VOCAB / ".swap.md").write_text("x")
    (tmp_path / VOCAB / "folder").mkdir()

    assert files.names(VOCAB) == (NAME,)


def test_a_file_that_is_not_text_reads_as_nothing(tmp_path: Path) -> None:
    files = _files(tmp_path)
    files.write(VOCAB, NAME, LIST)
    (tmp_path / VOCAB / "photo.png").write_bytes(bytes([0xFF, 0xD8, 0xFF, 0xE0]))

    assert files.read(VOCAB, "photo.png") is None
    assert files.read(VOCAB, NAME) == LIST


@pytest.mark.parametrize(
    "name",
    ["../escape.md", "/etc/passwd", "sub/dir.md", "..", ".", ".hidden", "", "x" * 101],
)
def test_a_name_that_is_not_one_plain_name_is_refused(
    tmp_path: Path, name: str
) -> None:
    files = _files(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret")

    with pytest.raises(FileNameRejectedError):
        files.write(VOCAB, name, "pwned")
    with pytest.raises(FileNameRejectedError):
        files.read(VOCAB, name)
    with pytest.raises(FileNameRejectedError):
        files.write(VOCAB, name, None)

    assert outside.read_text() == "secret"


# A German vocabulary field names its lists in German, and a rule written in ASCII
# would refuse the one name the reader most wants.
def test_a_name_in_the_readers_own_language_is_kept(tmp_path: Path) -> None:
    files = _files(tmp_path)

    files.write(VOCAB, "Einheit 3 Wörter.md", LIST)

    assert files.names(VOCAB) == ("Einheit 3 Wörter.md",)
    assert files.read(VOCAB, "Einheit 3 Wörter.md") == LIST


def test_a_write_over_the_cap_is_refused_and_keeps_nothing(tmp_path: Path) -> None:
    files = _files(tmp_path, cap=16)

    with pytest.raises(FileTooLargeToKeepError) as refused:
        files.write(VOCAB, NAME, "x" * 17)

    assert "16" in str(refused.value)
    assert files.read(VOCAB, NAME) is None


def test_a_write_the_cap_allows_lands_whole(tmp_path: Path) -> None:
    files = _files(tmp_path, cap=16)

    files.write(VOCAB, NAME, "x" * 16)

    assert files.read(VOCAB, NAME) == "x" * 16


def test_a_directory_that_cannot_be_read_fails_rather_than_reading_empty(
    tmp_path: Path,
) -> None:
    files = _files(tmp_path)
    files.write(VOCAB, NAME, LIST)
    (tmp_path / VOCAB).chmod(0o000)

    try:
        with pytest.raises(FieldFileError):
            files.names(VOCAB)
    finally:
        (tmp_path / VOCAB).chmod(0o700)
