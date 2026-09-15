"""What a plugin kept for the conversation the work happening right now belongs to.

A tool call is the one place a plugin's own code runs inside a turn, and the state that
turn is answering on is already in the step's hands there. Binding it for the length of
the call is what lets a plugin read what it kept last turn without being handed it: a
plugin cannot see the conversation it is running in, so a parameter would be a value
nobody could fill.

A context variable rather than a field on the host, because there is one host per plugin
for the life of the process, and two turns answering at once must not share what they
kept.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

Kept = dict[str, dict[str, str]]

_kept: ContextVar[Kept | None] = ContextVar("_kept", default=None)


@contextmanager
def bound(kept: Kept) -> Iterator[None]:
    """Run this block over what these plugins kept, and leave what is outside it alone.

    Written into rather than replaced: what the block keeps is in `kept` when it ends,
    which is how the step that bound it carries the writes back into the turn's state.

    Reset rather than cleared, so a loop delegated inside a call does not take the
    call's own store away from whatever runs after it.
    """
    token = _kept.set(kept)
    try:
        yield
    finally:
        _kept.reset(token)


def read(plugin: str, name: str) -> str | None:
    """What this plugin kept under this name, or nothing.

    Outside a binding there is no conversation to read from, and the answer is nothing
    rather than a failure: a plugin doing housekeeping as it loads is not in a turn.

    Args:
        plugin: The name cora loaded the plugin under, which is what its keys hang from.
    """
    kept = _kept.get()
    if kept is None:
        return None
    return kept.get(plugin, {}).get(name)


def keep(plugin: str, name: str, value: str | None) -> None:
    """Keep `value` for this plugin under this name, or drop the name given nothing.

    Outside a binding nothing is kept, as a step taken outside a call is dropped.

    Args:
        plugin: The name cora loaded the plugin under, which is what its keys hang from.
        value: The text to keep. `None` drops the name, which is the only way a plugin
            has of forgetting one — a name left holding nothing would travel through a
            checkpoint and come back as a value that is not text.
    """
    kept = _kept.get()
    if kept is None:
        return
    if value is None:
        kept.get(plugin, {}).pop(name, None)
        return
    kept.setdefault(plugin, {})[name] = value
