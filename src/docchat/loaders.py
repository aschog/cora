from collections.abc import Callable

from docchat.errors import UnreadableFileError


def load_txt(data: bytes, filename: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnreadableFileError(filename) from exc


LOADERS: dict[str, Callable[[bytes, str], str]] = {
    ".txt": load_txt,
    ".md": load_txt,
}
