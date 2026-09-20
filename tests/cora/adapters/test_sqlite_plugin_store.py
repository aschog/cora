import pathlib
import sqlite3

import pytest

from cora.adapters.sqlite_plugin_store import SqlitePluginStore
from cora.domain.errors import PluginStoreError


@pytest.fixture
def path(tmp_path: pathlib.Path) -> str:
    return str(tmp_path / "cora.sqlite")


def test_what_was_kept_survives_a_new_adapter_over_the_same_file(path: str) -> None:
    """The restart in miniature: what "outlives the process" means."""
    SqlitePluginStore.at(path).keep("vocab", "schedule", "help due 2026-09-26")

    assert SqlitePluginStore.at(path).read("vocab", "schedule") == "help due 2026-09-26"


def test_two_plugins_keeping_under_one_name_keep_two_values(path: str) -> None:
    store = SqlitePluginStore.at(path)

    store.keep("vocab", "count", "12")
    store.keep("fitness", "count", "3")

    assert (store.read("vocab", "count"), store.read("fitness", "count")) == ("12", "3")


def test_a_name_nothing_was_kept_under_reads_as_nothing(path: str) -> None:
    assert SqlitePluginStore.at(path).read("vocab", "never") is None


def test_keeping_nothing_under_a_name_drops_it(path: str) -> None:
    store = SqlitePluginStore.at(path)
    store.keep("vocab", "schedule", "something")

    store.keep("vocab", "schedule", None)

    assert store.read("vocab", "schedule") is None


def test_dropping_a_name_nothing_was_kept_under_is_no_failure(path: str) -> None:
    SqlitePluginStore.at(path).keep("vocab", "never", None)


def test_a_store_that_cannot_be_reached_fails_rather_than_losing_the_write(
    path: str,
) -> None:
    """A write that silently went nowhere reads back as never having been made, which
    is the one answer a plugin cannot tell from an empty store."""
    store = SqlitePluginStore.at(path)
    store.close()

    with pytest.raises(PluginStoreError):
        store.keep("vocab", "schedule", "lost")


def test_a_file_that_is_not_a_store_is_refused_as_one(tmp_path: pathlib.Path) -> None:
    not_a_store = tmp_path / "prose.sqlite"
    not_a_store.write_bytes(b"this is not a database")

    with pytest.raises((PluginStoreError, sqlite3.DatabaseError)):
        SqlitePluginStore.at(str(not_a_store)).read("vocab", "schedule")
