import sqlite3

from langgraph.store.sqlite import SqliteStore

from cora.adapters.sqlite_store import connect
from cora.adapters.translating import translating
from cora.domain.errors import PluginStoreError

KEPT = "kept"
TEXT = "text"
PAGE = 100


_translate_errors = translating((sqlite3.Error, OSError), PluginStoreError)


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

    @_translate_errors
    def forget(self, plugin: str) -> None:
        # Searched a page at a time rather than counted first: the store offers no
        # count, and a plugin's names are few enough that one page is usually all of
        # them.
        while found := self._store.search((KEPT, plugin), limit=PAGE):
            for item in found:
                self._store.delete((KEPT, plugin), item.key)

    def close(self) -> None:
        self._store.conn.close()
