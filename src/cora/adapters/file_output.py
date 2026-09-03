import pathlib
from dataclasses import dataclass

from cora.domain.errors import OutputStoreError
from cora.ports.plugin import ToolRefusal

ESCAPES = (
    "'{name}' is not a name I can write: it has to name a file that stays under the "
    "output location, not a path out of it"
)
"""What a plugin is told when a name would leave the root. Worded for the model, which
is what reads a refused call — and it says what a name may be rather than only what it
may not."""


@dataclass(frozen=True)
class FileOutput:
    """The output port over one directory of files.

    The root is made on the first write rather than at assembly: a deployment that
    configures a location and never writes to it should not find an empty directory it
    did not ask for.
    """

    root: pathlib.Path

    @classmethod
    def at(cls, path: str) -> "FileOutput":
        return cls(root=pathlib.Path(path))

    def write(self, name: str, text: str) -> str:
        """Keep the text under the root, refusing any name that would leave it.

        Raises:
            ToolRefusal: The name is blank, is not a path at all, or resolves outside
                the root.
            OutputStoreError: The file could not be written.
        """
        root = self.root.resolve()
        landing = self._under(root, name)
        try:
            landing.parent.mkdir(parents=True, exist_ok=True)
            # Named rather than left to the locale: an itinerary has em-dashes and place
            # names in it, and a host whose preferred encoding is not UTF-8 could not
            # write one. `UnicodeError` is caught with it because it is a `ValueError`,
            # so it would otherwise escape the one failure this port says it raises.
            landing.write_text(text, encoding="utf-8")
        except (OSError, UnicodeError) as unwritable:
            raise OutputStoreError from unwritable
        return str(landing)

    def _under(self, root: pathlib.Path, name: str) -> pathlib.Path:
        """Where this name lands, once it is known to stay under the root.

        Resolved before it is compared, so `..`, an absolute path and a symlink are all
        read as what they would really reach — a check on the spelling of a name is a
        check a second spelling gets round.

        Raises:
            ToolRefusal: The name is blank, cannot be resolved at all, or resolves to
                the root itself or outside it.
        """
        if not name.strip():
            raise ToolRefusal(ESCAPES.format(name=name))
        try:
            landing = (root / name).resolve()
        except ValueError as unresolvable:
            # A NUL byte makes a string something no filesystem can look up. Refused as
            # the bad name it is, rather than raised as a kind the port never named.
            raise ToolRefusal(ESCAPES.format(name=name)) from unresolvable
        if landing == root or not landing.is_relative_to(root):
            raise ToolRefusal(ESCAPES.format(name=name))
        return landing
