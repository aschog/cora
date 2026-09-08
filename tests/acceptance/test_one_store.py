import sqlite3
from pathlib import Path

import pytest

from app_config import store_config
from cora.app.assembly import build
from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Turn

pytestmark = pytest.mark.integration


def test_everything_cora_keeps_for_itself_is_in_the_one_file_the_setting_names(
    tmp_path: Path,
) -> None:
    """What the change is for, stated once: the facts, the turns, the checkpoints and
    the passages in one database, and no second one beside it."""
    app = build(store_config(tmp_path))
    assert app.memory is not None and app.conversations is not None

    app.memory.remember("lifts on tuesdays")
    app.conversations.record(
        "t1", Turn(question="How much protein?", result=ChatResult(answer="1.6 g"))
    )
    app.knowledge_base.add_file(b"Deadlifts train the posterior chain. " * 40, "l.txt")

    store = tmp_path / "cora.sqlite"
    with sqlite3.connect(str(store)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type in ('table', 'view')"
            )
        }

    assert sorted(path.name for path in tmp_path.glob("*.sqlite")) == ["cora.sqlite"]
    assert {"store", "cora_turns", "checkpoints", "cora_passages"} <= tables
    assert [fact.text for fact in app.memory.recall()] == ["lifts on tuesdays"]
    assert [turn.question for turn in app.conversations.turns("t1")] == [
        "How much protein?"
    ]
    assert app.knowledge_base.list_sources() == ["l.txt"]


def test_forgetting_a_fact_leaves_the_turns_and_the_passages(tmp_path: Path) -> None:
    """The other direction of one file: what a rail forgets is its own rows, and the
    two stores sharing the database are untouched by it."""
    app = build(store_config(tmp_path))
    assert app.memory is not None and app.conversations is not None
    app.memory.remember("lifts on tuesdays")
    app.conversations.record("t1", Turn(question="q", result=ChatResult(answer="a")))
    app.knowledge_base.add_file(b"Deadlifts train the posterior chain. " * 40, "l.txt")

    app.memory.clear()

    assert app.memory.recall() == ()
    assert [turn.question for turn in app.conversations.turns("t1")] == ["q"]
    assert app.knowledge_base.list_sources() == ["l.txt"]
