import re
from collections.abc import Callable
from functools import wraps
from pathlib import Path

from cora.domain.errors import (
    FieldFileError,
    FileNameRejectedError,
    FileTooLargeToKeepError,
)
from cora.ports.files import MOST_BYTES

# A name a person types for a list of their own: letters of any language, digits, and
# the three marks a filename carries. It has to begin with a letter or a digit, which
# is what keeps a dotfile, `.` and `..` out without naming any of them.
PLAIN_NAME = re.compile(r"[^\W_][\w .\-]*\Z")
MOST_CHARACTERS = 100


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except OSError as error:
            raise FieldFileError() from error

    return wrapper


class DirectoryFiles:
    """One directory per field, holding a text file per name the plugin keeps.

    A directory rather than a row, because these are files the user opens and edits:
    what a plugin keeps here is the user's own data in the user's own hands, and a
    schema in a database would put it behind cora.

    The name is checked before it reaches the filesystem, not sanitised into something
    else: a name that would leave the directory is a caller's mistake or an attack, and
    quietly writing it somewhere near is worse than refusing it.
    """

    def __init__(self, root: Path, cap: int = MOST_BYTES) -> None:
        self._root = root
        self._cap = cap

    @classmethod
    def at(cls, path: str, cap: int = MOST_BYTES) -> "DirectoryFiles":
        return cls(Path(path), cap)

    @_translate_errors
    def names(self, scope: str) -> tuple[str, ...]:
        folder = self._root / _plain(scope)
        if not folder.is_dir():
            return ()
        # Only names this store could have written. A directory on a real machine also
        # holds what the machine put there — `.DS_Store`, an editor's swap file — and a
        # listing that returned one would hand back a name its own reader refuses.
        return tuple(
            sorted(
                each.name
                for each in folder.iterdir()
                if each.is_file() and PLAIN_NAME.match(each.name)
            )
        )

    @_translate_errors
    def read(self, scope: str, name: str) -> str | None:
        held = self._at(scope, name)
        if not held.is_file():
            return None
        try:
            return held.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Not text, so not a file this store wrote — a photo dropped in the
            # directory reads as nothing rather than breaking every caller that is
            # walking the field. Listing filters what it can see; this is the rest.
            return None

    @_translate_errors
    def write(self, scope: str, name: str, text: str | None) -> None:
        held = self._at(scope, name)
        if text is None:
            held.unlink(missing_ok=True)
            return
        written = text.encode("utf-8")
        if len(written) > self._cap:
            raise FileTooLargeToKeepError(self._cap)
        held.parent.mkdir(parents=True, exist_ok=True)
        held.write_bytes(written)

    def _at(self, scope: str, name: str) -> Path:
        return self._root / _plain(scope) / _plain(name)


def _plain(name: str) -> str:
    if len(name) > MOST_CHARACTERS or not PLAIN_NAME.match(name):
        raise FileNameRejectedError(name)
    return name
