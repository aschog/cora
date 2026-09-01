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
    positions in it. The upload's hash is in the filename, which is what makes the
    store its own index: reading an upload is finding the file that carries it, and one
    filename uploaded twice is two files rather than one overwritten.
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
        found = sorted(self._folder(scope).glob(f"*-{upload[:HASH_LENGTH]}.md"))
        if not found:
            return None
        return found[0].read_text(encoding="utf-8")

    def _folder(self, scope: str) -> Path:
        if not BARE_NAME.match(scope):
            raise DocumentStoreError()
        return self._root / scope

    def _named(self, filename: str, upload: str) -> str:
        stem = UNSAFE.sub("-", Path(filename).stem).strip("-") or "document"
        return f"{stem}-{upload[:HASH_LENGTH]}.md"
