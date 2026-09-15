import sqlite3
import time
import uuid
from collections.abc import Callable
from functools import wraps

from langgraph.store.sqlite import SqliteStore

from cora.adapters.sqlite_store import connect
from cora.domain.errors import MemoryStoreError
from cora.ports.memory import Fact

MEMORIES = "memories"
DEFAULT_USER = "local"
TEXT = "text"
PAGE = 100
RECALL_LIMIT = 100


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except (sqlite3.Error, OSError) as error:
            # `OSError` is the directory the store could not be made in.
            raise MemoryStoreError() from error

    return wrapper


def _ordinal() -> str:
    return f"{time.time_ns():020d}-{uuid.uuid4().hex[:8]}"


class SqliteStoreMemory:
    """LangGraph's store, holding one user's facts under its own namespace. The
    connection is long-lived on purpose: `SqliteStore.from_conn_string` closes on
    exit, which is the wrong shape for an app that outlives one turn."""

    def __init__(self, store: SqliteStore, user: str = DEFAULT_USER) -> None:
        self._store = store
        self._namespace = (MEMORIES, user)

    @classmethod
    @_translate_errors
    def at(cls, path: str, user: str = DEFAULT_USER) -> "SqliteStoreMemory":
        connection = connect(path)
        store = SqliteStore(connection)
        store.setup()
        return cls(store, user)

    @_translate_errors
    def remember(self, text: str) -> None:
        self._store.put(self._namespace, _ordinal(), {TEXT: text})

    def recall(self) -> tuple[Fact, ...]:
        kept = self._everything()
        return kept[max(len(kept) - RECALL_LIMIT, 0) :]

    @_translate_errors
    def _everything(self) -> tuple[Fact, ...]:
        found = []
        offset = 0
        while True:
            page = self._store.search(self._namespace, limit=PAGE, offset=offset)
            found.extend(page)
            if len(page) < PAGE:
                break
            offset += PAGE
        return tuple(
            Fact(key=item.key, text=str(item.value[TEXT]))
            for item in sorted(found, key=lambda item: item.key)
        )

    @_translate_errors
    def forget(self, key: str) -> None:
        self._store.delete(self._namespace, key)

    def clear(self) -> None:
        for fact in self._everything():
            self.forget(fact.key)

    def close(self) -> None:
        self._store.conn.close()
