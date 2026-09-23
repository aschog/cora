import pytest

from cora.plugins.documents.ingestion import Refused, ingest
from cora.plugins.documents.loaders import LOADERS, load_pdf, load_txt
from pdf_fixtures import make_pdf_bytes


def test_utf8_txt_bytes_decode_to_text() -> None:
    data = "Héllo, wörld.\nSecond line.".encode()

    assert load_txt(data, "notes.txt") == "Héllo, wörld.\nSecond line."


def test_undecodable_txt_bytes_are_refused_as_unreadable() -> None:
    with pytest.raises(Refused, match="unreadable") as excinfo:
        load_txt(b"\xff\xfe\x00invalid utf-8", "notes.txt")

    assert "notes.txt" in excinfo.value.said


def test_multi_page_pdf_joins_pages_in_order_with_paragraph_break() -> None:
    data = make_pdf_bytes("First page.", "Second page.", "Third page.")

    assert load_pdf(data, "doc.pdf") == "First page.\n\nSecond page.\n\nThird page."


def test_corrupt_pdf_bytes_are_refused_as_unreadable() -> None:
    with pytest.raises(Refused, match="unreadable") as excinfo:
        load_pdf(b"%PDF-1.4 not really a pdf", "broken.pdf")

    assert "broken.pdf" in excinfo.value.said


def test_image_only_pdf_is_refused_as_empty() -> None:
    with pytest.raises(Refused, match="no readable text"):
        ingest(make_pdf_bytes("", ""), "scanned.pdf", LOADERS)
