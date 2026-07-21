"""Application-wide error hierarchy.

Every error carries a user-presentable message; the UI shell renders it
verbatim, so no failure ever reaches the user as a stack trace.
"""

from collections.abc import Iterable


class DocChatError(Exception):
    """Base error for all application failures."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


class IngestionError(DocChatError):
    """A document could not be ingested; the message names the file.

    Subclasses set ``reason`` to describe the specific failure.
    """

    reason = "the file could not be ingested."

    def __init__(self, filename: str) -> None:
        super().__init__(f"Could not process '{filename}': {self.reason}")
        self.filename = filename


class UnsupportedFileTypeError(IngestionError):
    reason = "unsupported file type."

    def __init__(self, filename: str, supported: Iterable[str] = ()) -> None:
        formats = ", ".join(sorted(supported))
        if formats:
            self.reason = f"unsupported file type (supported: {formats})."
        super().__init__(filename)


class FileTooLargeError(IngestionError):
    reason = "the file is too large."


class EmptyDocumentError(IngestionError):
    reason = "the document has no readable text."


class UnreadableFileError(IngestionError):
    reason = "the file is corrupted or unreadable."


class AdapterError(DocChatError):
    message = "The document service is temporarily unavailable. Please try again."

    def __init__(self) -> None:
        super().__init__(self.message)


class EmbeddingError(AdapterError):
    message = "Could not generate embeddings for the document. Please try again."


class RetrievalError(AdapterError):
    message = "The knowledge base is temporarily unavailable. Please try again."
