"""Where a command of the model's is run: one field's directory, and what came back."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Ran:
    """What one command came to.

    `output` is what it printed on both streams, in order, cut where `cut` says so.
    `stopped` says the deployment's time ran out before the command did, and `code` is
    what the command exited with — meaningless where it was stopped.
    """

    output: str
    code: int = 0
    cut: bool = False
    stopped: bool = False


class Shell(Protocol):
    """Runs a command with a field's directory as its working directory.

    The field is named by scope, the way its files are: the directory is the same one
    the field's files are kept in, so what a command lists is what a read would read.
    A field that has no directory yet is given one, because a command that cannot
    start is a worse answer than an empty listing.

    Raises:
        FieldFileError: The directory could not be made or the command could not start.
        FileNameRejectedError: The scope is not one plain name.
    """

    def run(self, scope: str, command: str) -> Ran:
        """Run `command` in the field's directory, and answer with what it came to."""
        ...
