import re
from collections.abc import Callable
from functools import wraps
from pathlib import Path

from cora.domain.errors import DocumentStoreError

HASH_LENGTH = 12
"""How much of an upload's hash names its file. Long enough that two uploads never
collide, short enough that the name still reads as the document's."""
BARE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
"""What a scope may be called, because a scope is a directory here. The name reaches
this store from an upload, so anything that could walk out of the root is refused
before a byte is written."""
UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
UPLOAD = re.compile(r"[0-9a-f]{64}\Z")
"""What an upload is named by: the whole of the hash of the bytes it arrived as."""


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except OSError as error:
            raise DocumentStoreError() from error

    return wrapper


class FileDocuments:
    """One Markdown file per source, under a directory named for its scope.

    The file holds the cleaned text and nothing else, because a citation's offsets are
    positions in it. The head of the upload's hash is in the filename, which is what
    makes the store its own index and what makes one filename uploaded twice two files
    rather than one overwritten. It is short so the directory reads well, and short is
    not a name to accept from a URL — so an upload is read by the whole of what it is,
    and the head only narrows the search for it.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    @classmethod
    def at(cls, path: str) -> "FileDocuments":
        return cls(Path(path))

    @_translate_errors
    def keep(self, scope: str, upload: str, filename: str, text: str) -> None:
        folder = self._folder(scope)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / self._named(filename, upload)).write_text(text, encoding="utf-8")

    @_translate_errors
    def read(self, scope: str, upload: str) -> str | None:
        head = _head(upload)
        if head is None or not BARE_NAME.match(scope):
            return None
        for found in sorted((self._root / scope).glob(f"*-{head}.md")):
            return found.read_text(encoding="utf-8")
        return None

    @_translate_errors
    def forget(self, scope: str, upload: str) -> None:
        head = _head(upload)
        if head is None or not BARE_NAME.match(scope):
            return
        for found in sorted((self._root / scope).glob(f"*-{head}.md")):
            found.unlink()

    def _folder(self, scope: str) -> Path:
        if not BARE_NAME.match(scope):
            raise DocumentStoreError()
        return self._root / scope

    def _named(self, filename: str, upload: str) -> str:
        stem = UNSAFE.sub("-", Path(filename).stem).strip("-") or "document"
        return f"{stem}-{upload[:HASH_LENGTH]}.md"


def _head(upload: str) -> str | None:
    """What names this upload's file, or nothing where it is not an upload at all."""
    return upload[:HASH_LENGTH] if UPLOAD.match(upload) else None
