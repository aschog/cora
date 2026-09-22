import pathlib
import sqlite3

import pytest

from cora.adapters.sqlite_store_memory import RECALL_LIMIT, SqliteStoreMemory
from cora.domain.errors import AdapterError


@pytest.fixture
def path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "memory.sqlite")


def test_a_fact_survives_a_new_adapter_over_the_same_file(path: str) -> None:
    SqliteStoreMemory.at(path).remember("trains on Tuesdays")

    facts = SqliteStoreMemory.at(path).recall()

    assert [fact.text for fact in facts] == ["trains on Tuesdays"]


def test_facts_come_back_oldest_first_under_stable_keys(path: str) -> None:
    memory = SqliteStoreMemory.at(path)

    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    keys = [fact.key for fact in memory.recall()]
    assert [fact.text for fact in memory.recall()] == [
        "trains on Tuesdays",
        "is vegetarian",
    ]
    assert keys == [fact.key for fact in SqliteStoreMemory.at(path).recall()]


def test_forgetting_removes_that_fact_alone(path: str) -> None:
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    memory.forget(memory.recall()[0].key)

    assert [fact.text for fact in SqliteStoreMemory.at(path).recall()] == [
        "is vegetarian"
    ]


def test_clearing_removes_them_all(path: str) -> None:
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.remember("is vegetarian")

    memory.clear()

    assert SqliteStoreMemory.at(path).recall() == ()


def test_another_user_recalls_nothing(path: str) -> None:
    SqliteStoreMemory.at(path, user="ada").remember("trains on Tuesdays")

    assert SqliteStoreMemory.at(path, user="grace").recall() == ()
    assert len(SqliteStoreMemory.at(path, user="ada").recall()) == 1


def test_a_broken_database_surfaces_as_an_adapter_error(path: str) -> None:
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.close()

    with pytest.raises(AdapterError):
        memory.recall()
    with pytest.raises(AdapterError):
        memory.remember("is vegetarian")


MORE_THAN_A_PAGE = 150


def test_recall_returns_the_newest_facts_when_there_are_more_than_it_shows(
    path: str,
) -> None:
    memory = SqliteStoreMemory.at(path)
    for number in range(MORE_THAN_A_PAGE):
        memory.remember(f"fact {number}")

    facts = memory.recall()

    assert len(facts) == RECALL_LIMIT
    assert facts[-1].text == f"fact {MORE_THAN_A_PAGE - 1}"
    assert facts[0].text == f"fact {MORE_THAN_A_PAGE - RECALL_LIMIT}"


def test_the_store_shares_the_file_in_write_ahead_mode(
    tmp_path: pathlib.Path,
) -> None:
    memory = SqliteStoreMemory.at(str(tmp_path / "cora.sqlite"))

    with sqlite3.connect(str(tmp_path / "cora.sqlite")) as reading:
        [(mode,)] = reading.execute("pragma journal_mode")

    memory.close()
    assert mode == "wal"
