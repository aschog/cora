"""What a plugin keeps for good, and the view of it one plugin holds.

Two protocols because there are two callers. The deployment builds a `Store`, which is
keyed by plugin as well as by name — that is what keeps one plugin's names away from
another's. A plugin is handed a `Kept`, which is its own row of that store with the
plugin already filled in, because a plugin naming itself on every call is a plugin that
can name somebody else.

Not `State`, which lasts as long as the conversation a turn belongs to, and not
`Memory`, which is what cora knows about the user and says so in a brief.
"""

from typing import Protocol


class Kept(Protocol):
    """One plugin's own store, read and written by name.

    What is kept here outlives the turn, the conversation and the process. It is text:
    a plugin keeping a schedule or a count writes and reads its own, and what the text
    means is the plugin's business rather than cora's.
    """

    def read(self, name: str) -> str | None:
        """What this plugin kept under this name, or nothing where nothing was."""
        ...

    def keep(self, name: str, value: str | None) -> None:
        """Keep `value` under this name until something else is kept there.

        Args:
            value: The text to keep. `None` drops the name.
        """
        ...


class Store(Protocol):
    """Where every plugin's own store is kept, as the deployment holds it.

    Keyed by plugin and then by name, so two plugins choosing one name keep two values.

    Raises:
        StoreError: The store could not be reached. A write that cannot land is a
            failure rather than a silence, because a plugin reading nothing back would
            read it as never having kept anything.
    """

    def read(self, plugin: str, name: str) -> str | None:
        """What that plugin kept under that name, or nothing."""
        ...

    def keep(self, plugin: str, name: str, value: str | None) -> None:
        """Keep `value` for that plugin under that name, or drop the name given none."""
        ...
