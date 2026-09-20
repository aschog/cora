import sqlite3
from collections.abc import Callable
from functools import wraps

from langgraph.store.sqlite import SqliteStore

from cora.adapters.sqlite_store import connect
from cora.domain.errors import PluginStoreError

KEPT = "kept"
TEXT = "text"


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except (sqlite3.Error, OSError) as error:
            raise PluginStoreError() from error

    return wrapper


class SqlitePluginStore:
    """Every plugin's own store, in the file cora keeps its bookkeeping in.

    One namespace per plugin under `kept`, which is what separates one plugin's names
    from another's — the same separation the settings and the log already make.
    """

    def __init__(self, store: SqliteStore) -> None:
        self._store = store

    @classmethod
    @_translate_errors
    def at(cls, path: str) -> "SqlitePluginStore":
        connection = connect(path)
        store = SqliteStore(connection)
        store.setup()
        return cls(store)

    @_translate_errors
    def read(self, plugin: str, name: str) -> str | None:
        found = self._store.get((KEPT, plugin), name)
        return None if found is None else str(found.value[TEXT])

    @_translate_errors
    def keep(self, plugin: str, name: str, value: str | None) -> None:
        if value is None:
            self._store.delete((KEPT, plugin), name)
            return
        self._store.put((KEPT, plugin), name, {TEXT: value})

    def close(self) -> None:
        self._store.conn.close()
