"""Where a field keeps the files its plugin owns, which are not its documents.

Not `Documents`, which holds the text a citation opens onto and is chunked, embedded
and searched. These are the plugin's own data — a schedule, a list, a log — kept as
text a person can open in an editor, and nothing indexes them.

Keyed by scope rather than by plugin, the way documents are: a field is what the screen
addresses and what a person recognises, and a plugin loaded under two fields keeps two
sets.
"""

import re
from typing import Protocol

MOST_BYTES = 1_000_000

# A name a person types for a list of their own: letters of any language, digits, and
# the three marks a filename carries. It has to begin with a letter or a digit, which
# is what keeps a dotfile, `.` and `..` out without naming any of them.
_PLAIN_NAME = re.compile(r"[^\W_][\w .\-]*\Z")
MOST_CHARACTERS = 100


def plain_name(name: str) -> bool:
    """Whether this is one plain name, which is the only kind a field keeps.

    The rule itself rather than each implementation's own, because a listing and a
    reader that disagree hand back a name the reader then refuses.
    """
    return len(name) <= MOST_CHARACTERS and _PLAIN_NAME.match(name) is not None


class Files(Protocol):
    """Every field's own files, as the deployment holds them.

    Text under a plain name, one namespace per field. What the text means is the
    plugin's business rather than cora's.

    Raises:
        FieldFileError: The files could not be reached, on a listing, a read or a write.
        FileNameRejectedError: The name is not one plain name, so nothing was done.
    """

    def names(self, scope: str) -> tuple[str, ...]:
        """The names this field holds, sorted, or nothing where it holds none."""
        ...

    def read(self, scope: str, name: str) -> str | None:
        """The text kept under this name in this field, or nothing where none was."""
        ...

    def write(self, scope: str, name: str, text: str | None) -> None:
        """Keep `text` under this name in this field, replacing what was there.

        Args:
            text: The text to keep. `None` drops the name, and dropping a name nothing
                was kept under is not an error.

        Raises:
            FileTooLargeError: The text is over the deployment's cap, so nothing was
                kept and what was there is untouched.
        """
        ...
