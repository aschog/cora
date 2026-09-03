import pathlib
from dataclasses import dataclass

from cora.domain.errors import OutputStoreError
from cora.ports.plugin import ToolRefusal

ESCAPES = (
    "'{name}' is not a name I can write: it has to be a filename under the output "
    "location, not a path out of it"
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

        Resolved before it is compared, so `..` and an absolute path are both read as
        what they would really reach — a check on the spelling of a name is a check a
        second spelling gets round.

        Raises:
            ToolRefusal: The name is blank, or resolves outside the root.
            OutputStoreError: The file could not be written.
        """
        root = self.root.resolve()
        if not name.strip():
            raise ToolRefusal(ESCAPES.format(name=name))
        landing = (root / name).resolve()
        if landing == root or not landing.is_relative_to(root):
            raise ToolRefusal(ESCAPES.format(name=name))
        try:
            landing.parent.mkdir(parents=True, exist_ok=True)
            landing.write_text(text)
        except OSError as unwritable:
            raise OutputStoreError from unwritable
        return str(landing)
