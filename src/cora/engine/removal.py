"""Deleting a plugin, and everything that came into cora with it."""

import pathlib
import shutil

from cora.domain.errors import PluginRemovalError
from cora.engine.agent import Agent
from cora.engine.knowledge_base import KnowledgeBase
from cora.ports.files import Files
from cora.ports.host import DEFAULT_SCOPE, Listed
from cora.ports.store import Store

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
    files: Files | None = None,
    store: Store | None = None,
) -> None:
    """Delete one plugin from the plugins folder, with the data its fields hold.

    The data goes first and the entry last: the listing is what names the fields to
    empty, so a delete that failed part way leaves a plugin still listed and still
    deletable rather than one nobody can name. All three places a field's data sits are
    emptied — its documents, its own files, and what the plugin kept for good — because
    deleting a plugin deletes what it held and not only what it could be searched for.

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
        files: The files its fields keep. Without it the deployment keeps none.
        store: What it kept for good. Without it the deployment keeps none.

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
        if files is not None:
            for held in files.names(scope):
                files.write(scope, held, None)
    if store is not None:
        # Keyed by the module the plugin was loaded under, and a plugin that reaches
        # here was dropped in the folder — where that module is the entry's own name.
        store.forget(listed.name)
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
    if not fields or agent.conversations is None:
        return ()
    return tuple(
        conversation.thread_id
        for conversation in agent.conversations.opened()
        if agent.pinned(conversation.thread_id) in fields
    )


def _delete(name: str, entry: pathlib.Path) -> None:
    try:
        if entry.is_symlink() or not entry.is_dir():
            entry.unlink()
        else:
            shutil.rmtree(entry)
    except OSError as failed:
        raise PluginRemovalError(name, NOT_REMOVABLE) from failed
