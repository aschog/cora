import pathlib

import pytest

from cora.adapters.sqlite_store_memory import SqliteStoreMemory
from cora.domain.errors import AdapterError


@pytest.fixture
def path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "memory.sqlite")


def test_a_fact_survives_a_new_adapter_over_the_same_file(path: str) -> None:
    """The reopen in miniature: what the criterion means by "last session"."""
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
    """The namespace is the adapter's, so authentication later is a constructor
    argument rather than a change to the port."""
    SqliteStoreMemory.at(path, user="ada").remember("trains on Tuesdays")

    assert SqliteStoreMemory.at(path, user="grace").recall() == ()
    assert len(SqliteStoreMemory.at(path, user="ada").recall()) == 1


def test_a_fresh_path_creates_its_directories(tmp_path: pathlib.Path) -> None:
    nested = tmp_path / "does" / "not" / "exist" / "memory.sqlite"

    SqliteStoreMemory.at(str(nested)).remember("trains on Tuesdays")

    assert nested.exists()


def test_opening_the_same_file_twice_is_harmless(path: str) -> None:
    first = SqliteStoreMemory.at(path)
    second = SqliteStoreMemory.at(path)

    first.remember("trains on Tuesdays")

    assert [fact.text for fact in second.recall()] == ["trains on Tuesdays"]


def test_a_broken_database_surfaces_as_an_adapter_error(path: str) -> None:
    """So the friendly-failure path holds: the UI renders `user_message`, never a
    sqlite traceback."""
    memory = SqliteStoreMemory.at(path)
    memory.remember("trains on Tuesdays")
    memory.close()

    with pytest.raises(AdapterError):
        memory.recall()
    with pytest.raises(AdapterError):
        memory.remember("is vegetarian")
