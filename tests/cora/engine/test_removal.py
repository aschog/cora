import pathlib
from collections.abc import Iterator

import pytest

from cora.adapters.loaders import LOADERS
from cora.domain.agent_state import AgentState
from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Turn
from cora.domain.decision import Pending
from cora.domain.errors import PluginRemovalError
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.engine.removal import remove_plugin
from cora.ports.host import INSTRUCTIONS, Contributed, Listed
from fakes import (
    FakeConversations,
    FakeDocuments,
    FakeEmbedder,
    FakeFiles,
    FakeRetriever,
    FakeStore,
)

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


# A runner as removing reads one: the pin of each thread, and what it forgot.
class _Threads:
    def __init__(self, pins: dict[str, str] | None = None) -> None:
        self.pins = pins or {}
        self.forgotten: list[str] = []

    def pinned(self, thread_id: str) -> str | None:
        return self.pins.get(thread_id)

    def forget(self, thread_id: str) -> None:
        self.forgotten.append(thread_id)
        self.pins.pop(thread_id, None)

    def run(self, *args: object, **kwargs: object) -> Iterator[AgentState]:
        raise NotImplementedError

    def resume(self, *args: object, **kwargs: object) -> Iterator[AgentState]:
        raise NotImplementedError

    def pending(self, thread_id: str) -> Pending | None:
        return None


def _conversations(*threads: str) -> FakeConversations:
    kept = FakeConversations()
    for thread_id in threads:
        kept.record(thread_id, Turn(question="q", result=ChatResult(answer="a")))
    return kept


def _knowledge_base(
    documents: FakeDocuments | None = None, retriever: FakeRetriever | None = None
) -> KnowledgeBase:
    return KnowledgeBase(
        embedder=FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        loaders=LOADERS,
        documents=documents or FakeDocuments(),
    )


def _listed(name: str, source: str, *scopes: str) -> Listed:
    return Listed(
        name=name,
        source=source,
        contributions=tuple(
            Contributed(kind=INSTRUCTIONS, name="", scope=scope) for scope in scopes
        ),
    )


def _removing(
    name: str,
    *,
    folder: pathlib.Path | None,
    listing: tuple[Listed, ...],
    configured: tuple[str, ...] = (),
    knowledge_base: KnowledgeBase | None = None,
    threads: _Threads | None = None,
    conversations: FakeConversations | None = None,
    files: FakeFiles | None = None,
    store: FakeStore | None = None,
) -> None:
    remove_plugin(
        name,
        folder=folder,
        listing=listing,
        configured=configured,
        knowledge_base=knowledge_base or _knowledge_base(),
        agent=Agent(threads or _Threads(), conversations or _conversations()),
        files=files,
        store=store,
    )


def test_a_dropped_file_is_deleted(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
    )

    assert not dropped.exists()


def test_a_symlink_is_unlinked_and_its_target_is_left(tmp_path: pathlib.Path) -> None:
    elsewhere = tmp_path / "repository" / "travel"
    elsewhere.mkdir(parents=True)
    (elsewhere / "__init__.py").write_text(DROPPED)
    folder = tmp_path / "plugins"
    folder.mkdir()
    link = folder / "travel"
    link.symlink_to(elsewhere)

    _removing(
        "travel", folder=folder, listing=(_listed("travel", str(link), "travel"),)
    )

    assert not link.exists() and not link.is_symlink()
    assert (elsewhere / "__init__.py").exists()


def test_the_documents_and_passages_of_its_field_go(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    retriever, documents = FakeRetriever(), FakeDocuments()
    knowledge_base = _knowledge_base(documents, retriever)
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        knowledge_base=knowledge_base,
    )

    assert knowledge_base.list_sources("birds") == []
    assert retriever.sources("birds") == []
    assert documents.read("birds", "sightings.md") is None


def test_another_plugins_field_is_left_alone(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    other = tmp_path / "trips.py"
    other.write_text(DROPPED)
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")
    knowledge_base.add_file(b"Three days in Kyoto.", "kyoto.md", "travel")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(
            _listed("field_notes", str(dropped), "birds"),
            _listed("trips", str(other), "travel"),
        ),
        knowledge_base=knowledge_base,
    )

    assert knowledge_base.list_sources("travel") == ["kyoto.md"]
    assert other.exists()


def test_the_files_of_its_field_go(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    files = FakeFiles()
    files.write("birds", "waders.md", "Twelve at dawn.")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        files=files,
    )

    assert files.names("birds") == ()


def test_what_it_kept_for_good_goes(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    store = FakeStore()
    store.keep("field_notes", "schedule", "{}")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        store=store,
    )

    assert store.read("field_notes", "schedule") is None


def test_another_plugins_files_and_rows_are_left_alone(
    tmp_path: pathlib.Path,
) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    other = tmp_path / "trips.py"
    other.write_text(DROPPED)
    files, store = FakeFiles(), FakeStore()
    files.write("birds", "waders.md", "Twelve at dawn.")
    files.write("travel", "kyoto.md", "Three days.")
    store.keep("field_notes", "schedule", "{}")
    store.keep("trips", "schedule", "{}")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(
            _listed("field_notes", str(dropped), "birds"),
            _listed("trips", str(other), "travel"),
        ),
        files=files,
        store=store,
    )

    assert files.names("travel") == ("kyoto.md",)
    assert store.read("trips", "schedule") == "{}"


def test_a_conversation_pinned_to_the_field_goes(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    threads = _Threads({"watching": "birds", "planning": "travel"})
    conversations = _conversations("watching", "planning")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        threads=threads,
        conversations=conversations,
    )

    assert threads.forgotten == ["watching"]
    assert [each.thread_id for each in conversations.opened()] == ["planning"]


def test_a_plugin_named_in_the_environment_is_refused(tmp_path: pathlib.Path) -> None:
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    with pytest.raises(PluginRemovalError, match="fixed at start"):
        _removing(
            "field_notes",
            folder=tmp_path,
            listing=(_listed("field_notes", "cora.plugins.field_notes", "birds"),),
            knowledge_base=knowledge_base,
        )

    assert knowledge_base.list_sources("birds") == ["sightings.md"]
