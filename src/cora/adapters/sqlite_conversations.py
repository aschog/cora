import json
import pathlib
import sqlite3
from collections.abc import Callable
from dataclasses import asdict
from functools import wraps
from typing import Any, get_origin, get_type_hints

from cora.domain.chat_result import ChatResult
from cora.domain.citations import Citation
from cora.domain.conversation import Session, Turn
from cora.domain.errors import ConversationStoreError
from cora.domain.trace import TraceStep, step_kinds

STEPS = "steps"
"""The field a step keeps its own steps in, which is the one that nests."""

SCHEMA = (
    "create table if not exists turns ("
    "id integer primary key autoincrement, thread text not null, turn text not null)"
)


def _translate_errors[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    @wraps(method)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return method(*args, **kwargs)
        except sqlite3.Error as error:
            raise ConversationStoreError() from error

    return wrapper


class SqliteConversations:
    """One row per turn, in the order the turns were taken: the id the table hands out
    is what "the order they were taken" and "the newest conversation" both read off, so
    neither depends on a clock the tests would have to fake."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @classmethod
    @_translate_errors
    def at(cls, path: str) -> "SqliteConversations":
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            path, check_same_thread=False, isolation_level=None
        )
        connection.execute(SCHEMA)
        return cls(connection)

    @_translate_errors
    def record(self, thread_id: str, turn: Turn) -> None:
        self._connection.execute(
            "insert into turns (thread, turn) values (?, ?)",
            (thread_id, json.dumps(_as_data(turn))),
        )

    @_translate_errors
    def turns(self, thread_id: str) -> tuple[Turn, ...]:
        rows = self._connection.execute(
            "select turn from turns where thread = ? order by id", (thread_id,)
        ).fetchall()
        return tuple(_from_data(json.loads(row[0])) for row in rows)

    @_translate_errors
    def sessions(self) -> tuple[Session, ...]:
        rows = self._connection.execute(
            "select thread, turn from turns where id in "
            "(select min(id) from turns group by thread) "
            "order by (select max(id) from turns as newest where newest.thread = "
            "turns.thread) desc"
        ).fetchall()
        return tuple(
            Session(thread_id=row[0], opened_with=json.loads(row[1])["question"])
            for row in rows
        )

    def close(self) -> None:
        self._connection.close()


def _as_data(turn: Turn) -> dict[str, Any]:
    return {
        "question": turn.question,
        "answer": turn.result.answer,
        "citations": [asdict(citation) for citation in turn.result.citations],
        "trace": [_as_step(step) for step in turn.result.trace],
        "scopes": list(turn.result.scopes),
    }


def _from_data(data: dict[str, Any]) -> Turn:
    return Turn(
        question=str(data["question"]),
        result=ChatResult(
            answer=str(data["answer"]),
            citations=tuple(Citation(**found) for found in data["citations"]),
            trace=tuple(_step(step) for step in data["trace"]),
            # A turn recorded before a turn carried its fields has none, and reads back
            # as a turn in no named field — which is what it was.
            scopes=tuple(data.get("scopes", ())),
        ),
    )


def _as_step(step: TraceStep) -> dict[str, Any]:
    """One step as data, with the steps taken inside it kept as steps.

    `asdict` would flatten a child into a bare dict and lose which kind it was, so the
    children are written as this function writes any step: tagged with their kind.
    """
    # Every kind of step is a frozen dataclass; `TraceStep` itself is the ABC they
    # share, which ty cannot read as a dataclass instance.
    fields = asdict(step)  # ty: ignore[invalid-argument-type]
    if step.steps:
        fields[STEPS] = [_as_step(child) for child in step.steps]
    return {"kind": type(step).__name__, "fields": fields}


def _step(data: dict[str, Any]) -> TraceStep:
    """JSON has one sequence and a dataclass may want a tuple, so what a field is
    restored as is read off the kind's own declaration rather than guessed. The steps
    taken inside a step are restored as steps, however deep they go."""
    kind = {step.__name__: step for step in step_kinds()}[data["kind"]]
    declared = get_type_hints(kind)
    return kind(
        **{
            name: _restored(name, value, declared)
            for name, value in data["fields"].items()
        }
    )


def _restored(name: str, value: Any, declared: dict[str, Any]) -> Any:
    if name == STEPS:
        return tuple(_step(child) for child in value)
    if isinstance(value, list) and get_origin(declared.get(name)) is tuple:
        return tuple(value)
    return value
