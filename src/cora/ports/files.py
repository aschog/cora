"""Where a field keeps the files its plugin owns, which are not its documents.

Not `Documents`, which holds the text a citation opens onto and is chunked, embedded
and searched. These are the plugin's own data — a schedule, a list, a log — kept as
text a person can open in an editor, or as the bytes a reader uploaded, and nothing
indexes them.

Keyed by scope rather than by plugin, the way documents are: a field is what the screen
addresses and what a person recognises, and a plugin loaded under two fields keeps two
sets.
"""

import re
from typing import Protocol

from cora.domain.errors import FileNameRejectedError

MOST_BYTES = 10 * 1024 * 1024

# A name a person types for a list of their own: letters of any language, digits, and
# the three marks a filename carries. It has to begin with a letter or a digit, which
# is what keeps a dotfile, `.` and `..` out without naming any of them.
_PLAIN_NAME = re.compile(r"[^\W_][\w .\-]*\Z")
MOST_CHARACTERS = 100

# What a plain name has no room for, and the runs of space that dropping it leaves.
_NOT_PLAIN = re.compile(r"[^\w .\-]+")
_RUNS = re.compile(r" {2,}")


def plain_name(name: str) -> bool:
    """Whether this is one plain name, which is the only kind a field keeps.

    The rule itself rather than each implementation's own, because a listing and a
    reader that disagree hand back a name the reader then refuses.
    """
    return len(name) <= MOST_CHARACTERS and _PLAIN_NAME.match(name) is not None


def plain_from(name: str) -> str:
    """The nearest plain name to one a reader brought, for a name nobody typed.

    A file picked out of a browser is named whatever the machine it came from named it,
    and a name refused there is an upload the reader cannot make at all. So what the
    rule will not keep is dropped rather than refused — the name stays recognisable,
    and the extension with it, which is what says how to read the file.

    Refusing is still right where a plugin or the screen writes under a name somebody
    typed: there the name is a choice, and quietly keeping another is worse.

    Raises:
        FileNameRejectedError: Nothing of the name survives the rule.
    """
    kept = _NOT_PLAIN.sub("", name).lstrip("_. -")
    kept = _RUNS.sub(" ", kept).strip()
    if len(kept) > MOST_CHARACTERS:
        stem, dot, suffix = kept.rpartition(".")
        room = MOST_CHARACTERS - len(dot + suffix)
        kept = (
            stem[:room] + dot + suffix if dot and room > 0 else kept[:MOST_CHARACTERS]
        )
    if not plain_name(kept):
        raise FileNameRejectedError(name)
    return kept


class Files(Protocol):
    """Every field's own files, as the deployment holds them.

    Text or bytes under a plain name, one namespace per field. What a file means is
    the plugin's business rather than cora's.

    Raises:
        FieldFileError: The files could not be reached, on a listing, a read or a write.
        FileNameRejectedError: The name is not one plain name, so nothing was done.
    """

    def names(self, scope: str) -> tuple[str, ...]:
        """The names this field holds, sorted, or nothing where it holds none."""
        ...

    def read(self, scope: str, name: str) -> str | None:
        """The text kept under this name in this field, or nothing where none was.

        Nothing, too, where what is kept is not text: a file of bytes reads as absent
        here and as itself through `read_bytes`.
        """
        ...

    def read_bytes(self, scope: str, name: str) -> bytes | None:
        """The bytes kept under this name in this field, or nothing where none was."""
        ...

    def write(self, scope: str, name: str, text: str | bytes | None) -> None:
        """Keep `text` under this name in this field, replacing what was there.

        Args:
            text: The text or bytes to keep. `None` drops the name, and dropping a name
                nothing was kept under is not an error.

        Raises:
            FileTooLargeToKeepError: The text is over the deployment's cap, so nothing
                was kept and what was there is untouched.
        """
        ...
