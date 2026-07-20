from docchat.errors import UnreadableFileError


def load_txt(data: bytes, filename: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnreadableFileError(filename) from exc
