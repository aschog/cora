"""Generate valid PDF bytes in-memory for tests, no checked-in binaries.

Uses only pypdf's public writer API. Each page draws its text with a
Helvetica font so the loader's text extraction has something to read; a
page given an empty string stays blank (an image-only/scanned page).
"""

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)


def make_pdf_bytes(*page_texts: str) -> bytes:
    writer = PdfWriter()
    for text in page_texts:
        page = writer.add_blank_page(width=612, height=792)
        if text:
            _draw_text(page, text)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _draw_text(page: DictionaryObject, text: str) -> None:
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 50 700 Td ({escaped}) Tj ET".encode())
    page[NameObject("/Contents")] = stream
    page[NameObject("/MediaBox")] = ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(612), NumberObject(792)]
    )
