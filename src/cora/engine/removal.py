"""Deleting a plugin, and everything that came into cora with it."""

import pathlib
import shutil

from cora.domain.errors import PluginRemovalError
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.ports.host import DEFAULT_SCOPE, Listed

NOT_LOADED = "no plugin of that name is loaded"
FIXED_AT_START = "it is named in the environment, and is fixed at start"
NO_FOLDER = "this deployment reads no plugins folder"
NOT_REMOVABLE = "its entry could not be removed"


def remove_plugin(
    name: str,
    *,
    folder: pathlib.Path | None,
    listing: tuple[Listed, ...],
    configured: tuple[str, ...] = (),
    knowledge_base: KnowledgeBase,
    agent: Agent,
) -> None:
    """Delete one plugin from the plugins folder, with the data its fields hold.

    The documents go first and the entry last: the listing is what names the fields to
    empty, so a delete that failed part way leaves a plugin still listed and still
    deletable rather than one nobody can name.

    Args:
        name: What the plugin is called, as the listing calls it. It is resolved
            against the listing and never read as a path.
        folder: Where plugins are dropped. Nothing outside it is ever deleted.
        listing: Every plugin loaded, which is what says whose data this is and what
            another plugin still brings.
        configured: The fields the deployment named itself, which no plugin's deletion
            empties.
        knowledge_base: Where the documents of the fields going with it are kept.
        agent: The conversations, read for their pins and forgotten by both halves.

    Raises:
        PluginRemovalError: Nothing of that name is loaded, it is a module named in the
            environment and so has no entry to delete, or the entry could not be taken
            out of the folder.
    """
    listed = _loaded(name, listing)
    entry = _entry(listed, folder)
    fields = fields_going(listed, listing, configured)
    for scope in fields:
        for source in knowledge_base.list_sources(scope):
            knowledge_base.forget(scope, source)
    for thread_id in _pinned_to(fields, agent):
        agent.forget(thread_id)
    _delete(listed.name, entry)


def deletable(listed: Listed, folder: pathlib.Path | None) -> bool:
    """Whether this plugin is one this deployment can delete.

    The plugins folder is the only place a plugin can be deleted from: a module named
    in the environment is imported by name and returns at the next start, so there is
    no entry deleting it could take. The listing is what says which a plugin is, and
    this is the one rule that reads it — the refusal below and the listing the page
    draws its controls from are the same answer.
    """
    return folder is not None and pathlib.Path(listed.source).parent == folder


def _loaded(name: str, listing: tuple[Listed, ...]) -> Listed:
    for listed in listing:
        if listed.name == name:
            return listed
    raise PluginRemovalError(name, NOT_LOADED)


def _entry(listed: Listed, folder: pathlib.Path | None) -> pathlib.Path:
    """Where this plugin lies in the plugins folder, refusing one that lies elsewhere.

    Taken from the listing rather than built from the name, so nothing a caller sends
    can reach a path — and checked against the folder, so a plugin named as a module
    is refused rather than resolved to a directory that means nothing.
    """
    if folder is None:
        raise PluginRemovalError(listed.name, NO_FOLDER)
    if not deletable(listed, folder):
        raise PluginRemovalError(listed.name, FIXED_AT_START)
    return pathlib.Path(listed.source)


def fields_going(
    listed: Listed, listing: tuple[Listed, ...], configured: tuple[str, ...] = ()
) -> tuple[str, ...]:
    """The fields that leave with this plugin, which are the ones only it brings.

    Public because the page asks it before the reader answers: what a question about
    deleting says is lost has to be what deleting takes, and one rule read twice is a
    rule that can be read two ways.

    A field the deployment configured, or another loaded plugin registers under, is
    still offered once this one is gone — and documents in a field that is still
    offered belong to whatever still brings it. The field a bare cora answers in is
    always one of those: a plugin registering there says "in every field, and in none",
    and what is kept there was the user's before any plugin was loaded.
    """
    retained = (
        {DEFAULT_SCOPE}
        | set(configured)
        | {
            scope
            for other in listing
            if other.name != listed.name
            for scope in other.scopes
        }
    )
    return tuple(scope for scope in listed.scopes if scope not in retained)


def _pinned_to(fields: tuple[str, ...], agent: Agent) -> tuple[str, ...]:
    """Every conversation fixed to one of these fields, read one thread at a time.

    A pin is a key of the thread's own state rather than a column of the record, so
    finding them is a read per conversation — which is what the page already costs to
    reopen one. A deployment recording no turns has no conversation to enumerate, and
    so has none to delete. Neither has a thread that has never answered: it is listed
    nowhere and is reached by nothing, which is what deleting a conversation already
    leaves behind.
    """
    if not fields or agent.conversations is None:
        return ()
    return tuple(
        session.thread_id
        for session in agent.conversations.sessions()
        if agent.pinned(session.thread_id) in fields
    )


def _delete(name: str, entry: pathlib.Path) -> None:
    """Take the entry out of the folder, whatever shape it has.

    A symlink is unlinked rather than followed: it answers `is_dir()` when it points at
    one, and following it would delete the repository a deployment linked out of.

    What the filesystem raises is not a refusal a reader could act on — a second delete
    of one plugin finds the entry already gone — so it leaves here as cora's own
    sentence. Nothing else is lost by that: the entry goes last.

    Raises:
        PluginRemovalError: The entry could not be taken out of the folder.
    """
    try:
        if entry.is_symlink() or not entry.is_dir():
            entry.unlink()
        else:
            shutil.rmtree(entry)
    except OSError as failed:
        raise PluginRemovalError(name, NOT_REMOVABLE) from failed
