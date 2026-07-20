import pytest

from docchat.errors import UnreadableFileError
from docchat.loaders import LOADERS, load_pdf, load_txt
from pdf_fixtures import make_pdf_bytes


def test_utf8_txt_bytes_decode_to_text() -> None:
    data = "Héllo, wörld.\nSecond line.".encode()

    assert load_txt(data, "notes.txt") == "Héllo, wörld.\nSecond line."


def test_undecodable_txt_bytes_raise_unreadable_file_error() -> None:
    data = b"\xff\xfe\x00invalid utf-8"

    with pytest.raises(UnreadableFileError) as excinfo:
        load_txt(data, "notes.txt")

    assert "notes.txt" in excinfo.value.user_message


def test_txt_and_md_extensions_have_loaders() -> None:
    assert ".txt" in LOADERS
    assert ".md" in LOADERS


def test_loader_keys_are_lowercase() -> None:
    assert all(ext == ext.lower() for ext in LOADERS)


def test_single_page_pdf_round_trips_through_loader() -> None:
    data = make_pdf_bytes("Hello from a generated PDF.")

    assert load_pdf(data, "doc.pdf").strip() == "Hello from a generated PDF."


def test_md_bytes_load_with_markup_preserved() -> None:
    markdown = "# Title\n\n- **bold** item\n- [link](http://example.com)"
    data = markdown.encode()

    assert LOADERS[".md"](data, "notes.md") == markdown
