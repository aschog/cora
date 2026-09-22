import pytest

from cora.adapters.loaders import LOADERS, load_pdf, load_txt
from cora.domain.errors import EmptyDocumentError, UnreadableFileError
from cora.engine.ingestion import ingest
from pdf_fixtures import make_pdf_bytes


def test_utf8_txt_bytes_decode_to_text() -> None:
    data = "Héllo, wörld.\nSecond line.".encode()

    assert load_txt(data, "notes.txt") == "Héllo, wörld.\nSecond line."


def test_undecodable_txt_bytes_raise_unreadable_file_error() -> None:
    data = b"\xff\xfe\x00invalid utf-8"

    with pytest.raises(UnreadableFileError) as excinfo:
        load_txt(data, "notes.txt")

    assert "notes.txt" in excinfo.value.user_message


def test_multi_page_pdf_joins_pages_in_order_with_paragraph_break() -> None:
    data = make_pdf_bytes("First page.", "Second page.", "Third page.")

    assert load_pdf(data, "doc.pdf") == "First page.\n\nSecond page.\n\nThird page."


def test_corrupt_pdf_bytes_raise_unreadable_file_error() -> None:
    with pytest.raises(UnreadableFileError) as excinfo:
        load_pdf(b"%PDF-1.4 not really a pdf", "broken.pdf")

    assert "broken.pdf" in excinfo.value.user_message


def test_image_only_pdf_raises_empty_document_error() -> None:
    with pytest.raises(EmptyDocumentError):
        ingest(make_pdf_bytes("", ""), "scanned.pdf", LOADERS)
