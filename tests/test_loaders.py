import pytest

from docchat.errors import UnreadableFileError
from docchat.loaders import load_txt


def test_utf8_txt_bytes_decode_to_text() -> None:
    data = "Héllo, wörld.\nSecond line.".encode()

    assert load_txt(data, "notes.txt") == "Héllo, wörld.\nSecond line."


def test_undecodable_txt_bytes_raise_unreadable_file_error() -> None:
    data = b"\xff\xfe\x00invalid utf-8"

    with pytest.raises(UnreadableFileError) as excinfo:
        load_txt(data, "notes.txt")

    assert "notes.txt" in excinfo.value.user_message
