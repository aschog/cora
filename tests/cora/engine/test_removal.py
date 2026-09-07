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
from fakes import FakeConversations, FakeDocuments, FakeEmbedder, FakeRetriever

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


class _Threads:
    """A runner as removing reads one: the pin of each thread, and what it forgot."""

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
    """A store holding one turn per thread, which is what makes it a session."""
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
) -> None:
    remove_plugin(
        name,
        folder=folder,
        listing=listing,
        configured=configured,
        knowledge_base=knowledge_base or _knowledge_base(),
        agent=Agent(threads or _Threads(), conversations or _conversations()),
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


def test_a_dropped_package_is_deleted_whole(tmp_path: pathlib.Path) -> None:
    package = tmp_path / "interview"
    package.mkdir()
    (package / "__init__.py").write_text(DROPPED)
    (package / "prompts.py").write_text("TEXT = 'hello'\n")

    _removing(
        "interview",
        folder=tmp_path,
        listing=(_listed("interview", str(package), "interview"),),
    )

    assert not package.exists()


def test_a_symlink_is_unlinked_and_its_target_is_left(tmp_path: pathlib.Path) -> None:
    """A symlink to a directory answers `is_dir()`, so following it would delete the
    repository a deployment linked its plugins out of."""
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


def test_the_entry_stays_when_a_document_could_not_be_dropped(
    tmp_path: pathlib.Path,
) -> None:
    """The listing is what names the fields to empty, so a plugin whose data is still
    there is one that must still be listed — and deleting it again is the retry."""

    class _Failing(FakeDocuments):
        def forget(self, scope: str, upload: str) -> None:
            raise OSError("the file could not be deleted")

    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    knowledge_base = _knowledge_base(_Failing())
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    with pytest.raises(OSError):
        _removing(
            "field_notes",
            folder=tmp_path,
            listing=(_listed("field_notes", str(dropped), "birds"),),
            knowledge_base=knowledge_base,
        )

    assert dropped.exists()


def test_a_name_nothing_loaded_is_refused(tmp_path: pathlib.Path) -> None:
    with pytest.raises(PluginRemovalError, match="voyage"):
        _removing(
            "voyage", folder=tmp_path, listing=(_listed("travel", "x", "travel"),)
        )


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


def test_a_plugin_registering_two_fields_empties_both(tmp_path: pathlib.Path) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")
    knowledge_base.add_file(b"Two hares in the field.", "mammals.md", "hares")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds", "hares"),),
        knowledge_base=knowledge_base,
    )

    assert knowledge_base.list_sources("birds") == []
    assert knowledge_base.list_sources("hares") == []


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


def test_a_field_another_plugin_also_brings_keeps_its_documents(
    tmp_path: pathlib.Path,
) -> None:
    """The field is still offered once this plugin is gone, and documents in a field
    that is still offered belong to whatever still brings it."""
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    other = tmp_path / "ringing.py"
    other.write_text(DROPPED)
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(
            _listed("field_notes", str(dropped), "birds"),
            _listed("ringing", str(other), "birds"),
        ),
        knowledge_base=knowledge_base,
    )

    assert knowledge_base.list_sources("birds") == ["sightings.md"]


def test_a_configured_field_keeps_its_documents(tmp_path: pathlib.Path) -> None:
    """A field the deployment named is offered with no plugin behind it, so deleting
    one that registered under it empties nothing."""
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        configured=("birds",),
        knowledge_base=knowledge_base,
    )

    assert knowledge_base.list_sources("birds") == ["sightings.md"]


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
    assert [each.thread_id for each in conversations.sessions()] == ["planning"]


def test_a_conversation_pinned_to_nothing_is_left(tmp_path: pathlib.Path) -> None:
    """A pin is what marks a thread as the field's. One that holds none is the reader's
    own, whatever it was answered about."""
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    threads = _Threads({})
    conversations = _conversations("wondering")

    _removing(
        "field_notes",
        folder=tmp_path,
        listing=(_listed("field_notes", str(dropped), "birds"),),
        threads=threads,
        conversations=conversations,
    )

    assert threads.forgotten == []
    assert [each.thread_id for each in conversations.sessions()] == ["wondering"]


def test_a_plugin_with_no_field_goes_by_its_entry_alone(
    tmp_path: pathlib.Path,
) -> None:
    dropped = tmp_path / "screen.py"
    dropped.write_text(DROPPED)
    threads = _Threads({"watching": "birds"})
    conversations = _conversations("watching")
    knowledge_base = _knowledge_base()
    knowledge_base.add_file(b"Twelve waders at dawn.", "sightings.md", "birds")

    _removing(
        "screen",
        folder=tmp_path,
        listing=(_listed("screen", str(dropped)),),
        knowledge_base=knowledge_base,
        threads=threads,
        conversations=conversations,
    )

    assert not dropped.exists()
    assert knowledge_base.list_sources("birds") == ["sightings.md"]
    assert [each.thread_id for each in conversations.sessions()] == ["watching"]


def test_a_plugin_named_in_the_environment_is_refused(tmp_path: pathlib.Path) -> None:
    """A module is imported by name and returns at the next start, so there is no
    entry deleting it could take."""
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


def test_a_name_that_is_a_path_is_refused(tmp_path: pathlib.Path) -> None:
    """The name is resolved against the listing, so a path is a name nothing loaded
    under rather than somewhere to reach."""
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    listing = (_listed("field_notes", str(dropped), "birds"),)

    for named in ("../field_notes", str(dropped), "/etc/hosts"):
        with pytest.raises(PluginRemovalError):
            _removing(named, folder=tmp_path, listing=listing)

    assert dropped.exists()


def test_a_deployment_with_no_plugins_folder_deletes_nothing() -> None:
    with pytest.raises(PluginRemovalError, match="no plugins folder"):
        _removing("field_notes", folder=None, listing=(_listed("field_notes", "x"),))
