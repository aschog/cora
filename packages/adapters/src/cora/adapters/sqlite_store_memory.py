import pathlib
import sqlite3
import time
import uuid
from collections.abc import Callable
from functools import wraps

from langgraph.store.sqlite import SqliteStore

from cora.domain.errors import MemoryStoreError
from cora.ports.memory import Fact

MEMORIES = "memories"
DEFAULT_USER = "local"
TEXT = "text"
RECALL_LIMIT = 100
"""Enough facts that a user meets the limit long after the prompt would have. The
store pages, so this is the page — not a claim that a hundred is all there is."""


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except sqlite3.Error as error:
            raise MemoryStoreError() from error

    return wrapper


def _ordinal() -> str:
    """A key that sorts oldest first and collides with nothing. The store stamps
    `created_at` to the second, so two facts remembered in one breath would tie —
    ordering has to come from the key."""
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
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        store = SqliteStore(connection)
        store.setup()
        return cls(store, user)

    @_translate_errors
    def remember(self, text: str) -> None:
        self._store.put(self._namespace, _ordinal(), {TEXT: text})

    @_translate_errors
    def recall(self) -> tuple[Fact, ...]:
        found = self._store.search(self._namespace, limit=RECALL_LIMIT)
        return tuple(
            Fact(key=item.key, text=str(item.value[TEXT]))
            for item in sorted(found, key=lambda item: item.key)
        )

    @_translate_errors
    def forget(self, key: str) -> None:
        self._store.delete(self._namespace, key)

    def clear(self) -> None:
        for fact in self.recall():
            self.forget(fact.key)

    def close(self) -> None:
        self._store.conn.close()
