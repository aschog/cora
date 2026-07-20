from collections.abc import Callable
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from docchat.errors import UnreadableFileError


def load_txt(data: bytes, filename: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnreadableFileError(filename) from exc


def load_pdf(data: bytes, filename: str) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() for page in reader.pages]
    except PyPdfError as exc:
        raise UnreadableFileError(filename) from exc
    return "\n\n".join(page for page in pages if page)


LOADERS: dict[str, Callable[[bytes, str], str]] = {
    ".txt": load_txt,
    ".md": load_txt,
    ".pdf": load_pdf,
}
