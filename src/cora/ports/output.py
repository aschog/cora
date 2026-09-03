"""Where what an effect produced is kept, and what a name may not be."""

from typing import Protocol


class Output(Protocol):
    """The one place a deployment lets an effect write, as a plugin is handed it.

    A port rather than a path, so no plugin writes the confinement check itself: what a
    plugin holds is the ability to write *here*, and where here is stays the
    deployment's. One method, because a tool that produced something has one thing to do
    with it and the turn it ran in has to be able to say where it went.
    """

    def write(self, name: str, text: str) -> str:
        """Keep `text` under `name`, and answer with where it landed.

        Args:
            name: What to call it, relative to the output location. A name that would
                put the file outside that location is refused rather than resolved.
            text: The file's whole contents.

        Returns:
            Where the file is, as something the turn can tell the user.

        Raises:
            ToolRefusal: The name would not stay under the output location. A refusal
                rather than a failure: nothing broke, and the call answers for it.
            AdapterError: The file could not be written.
        """
        ...
