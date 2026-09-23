"""Where a reader's upload lands, and who is told that it did."""

from dataclasses import dataclass, field

from cora.domain.errors import UploadRefusedError
from cora.domain.trace import TraceStep
from cora.engine.events import dispatch
from cora.engine.plugin_set import Registry
from cora.ports.files import Files, plain_from
from cora.ports.host import UPLOADING


@dataclass(frozen=True)
class Intake:
    """An upload made a file of its field, and the plugins told of it in that field.

    The file is kept first, so a handler reads it the way it reads any file of the
    field; a refusal puts the field back as it was, so a refused upload leaves nothing
    behind — and takes nothing either, which matters now that a name a reader uploads
    may be one the field already holds. What is made of the file — indexed, parsed,
    ignored — is the handlers', and an upload nobody hears is a file kept and no more.
    """

    files: Files
    registry: Registry = field(default_factory=Registry)

    def take(self, scope: str, name: str, data: bytes) -> str:
        """Land the file in the field, and run the upload handlers that field reaches.

        Answers with the name the field kept, which is what the reader will find it
        under and not always the name they picked it as.

        The name is made into one the field can keep rather than refused: a file is
        named by the machine it came from, and a reader cannot rename it on the way.

        Raises:
            UploadRefusedError: A handler refused it, in its sentence, or broke, in
                cora's. The field is as it was either way.
            FileNameRejectedError: Nothing of the name survives the rule; nothing kept.
            FileTooLargeToKeepError: The file is over the cap; nothing was kept.
            FieldFileError: The files could not be reached.
        """
        kept = plain_from(name)
        # What the name held before this upload, so a refusal can put it back. A field
        # holds one file per name, and the name a reader uploads is not theirs to
        # choose: an upload cora will not take must not take their file with it.
        stood = self.files.read_bytes(scope, kept)
        self.files.write(scope, kept, data)
        trace: list[TraceStep] = []
        try:
            dispatch(
                UPLOADING,
                kept,
                self.registry.handlers(UPLOADING, frozenset({scope})),
                trace,
                frozenset({scope}),
            )
        except UploadRefusedError:
            self.files.write(scope, kept, stood)
            raise
        return kept
