import pathlib
import sqlite3
from collections.abc import Callable
from functools import wraps

from cora.domain.errors import DocumentStoreError

SCHEMA = "create table if not exists documents (upload text primary key, text text)"


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except sqlite3.Error as error:
            raise DocumentStoreError() from error

    return wrapper


class SqliteDocuments:
    """One row per upload, keyed by the hash of the bytes it arrived as. The connection
    is long-lived for the same reason the memory store's is: the app outlives a turn."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    @_translate_errors
    def at(cls, path: str) -> "SqliteDocuments":
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        connection.execute(SCHEMA)
        return cls(connection)

    @_translate_errors
    def keep(self, upload: str, text: str) -> None:
        self._connection.execute(
            "insert into documents (upload, text) values (?, ?) "
            "on conflict(upload) do update set text = excluded.text",
            (upload, text),
        )

    @_translate_errors
    def read(self, upload: str) -> str | None:
        found = self._connection.execute(
            "select text from documents where upload = ?", (upload,)
        ).fetchone()
        return None if found is None else str(found[0])

    def close(self) -> None:
        self._connection.close()
