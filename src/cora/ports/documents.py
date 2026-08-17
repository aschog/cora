from typing import Protocol


class Documents(Protocol):
    """The text a citation's offsets point into, kept under the document's name. It is
    the *cleaned* text ingestion chunked, not the uploaded bytes: an offset means
    nothing against anything else."""

    def keep(self, name: str, text: str) -> None: ...

    def read(self, name: str) -> str | None: ...
