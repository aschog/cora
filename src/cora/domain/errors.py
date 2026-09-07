"""Application-wide error hierarchy.

Every error carries a user-presentable message; the UI shell renders it
verbatim, so no failure ever reaches the user as a stack trace.
"""

from collections.abc import Iterable

from cora.domain.trace import TraceStep


class CoreError(Exception):
    """Base error for all application failures.

    `step` is the step of a turn the failure came out of, filled in by whoever named
    that step and empty everywhere else — a failure outside a turn belongs to no step.
    `trace` is what the turn had done by then, filled in by whoever holds those steps
    when the turn ends before any state carries them out: a question refused on the way
    in still says which plugin refused it.
    """

    def __init__(self, user_message: str) -> None:
        """Carry the sentence the user is shown; there is no second, internal one."""
        super().__init__(user_message)
        self.user_message = user_message
        self.step = ""
        self.trace: tuple[TraceStep, ...] = ()


class IngestionError(CoreError):
    """A document could not be ingested; the message names the file.

    Subclasses set `reason` to describe the specific failure, and the name reaches the
    user because a refusal about one upload has to say which.
    """

    reason: str

    def __init__(self, filename: str) -> None:
        """Name the file in the message."""
        super().__init__(f"Could not process '{filename}': {self.reason}")


class UnsupportedFileTypeError(IngestionError):
    """The file's extension is not one the deployment has a loader for."""

    reason = "unsupported file type."

    def __init__(self, filename: str, supported: Iterable[str] = ()) -> None:
        """Say which formats would have worked, when the caller knows them.

        Args:
            filename: The upload that was refused.
            supported: The extensions the deployment reads. Omitted, the message says
                only that the type is unsupported.
        """
        formats = ", ".join(sorted(supported))
        if formats:
            self.reason = f"unsupported file type (supported: {formats})."
        super().__init__(filename)


class FileTooLargeError(IngestionError):
    """The upload is over the size the deployment accepts. Nothing was read."""

    reason = "the file is too large."


class EmptyDocumentError(IngestionError):
    """The file was read and held no text — a scan, or a document of images."""

    reason = "the document has no readable text."


class UnreadableFileError(IngestionError):
    """The bytes are not the format the extension claims, or are damaged."""

    reason = "the file is corrupted or unreadable."


class PluginLoadError(CoreError):
    """A plugin named in the configuration could not be loaded or was refused.

    Raised while the app is being assembled, so a misconfigured deployment fails at
    startup rather than mid-answer.
    """

    def __init__(self, plugin_name: str, reason: str) -> None:
        """Name the plugin and why it was refused — both reach the user."""
        super().__init__(f"Plugin '{plugin_name}' could not be loaded: {reason}.")


class PluginRemovalError(CoreError):
    """A plugin could not be deleted, or is not one this deployment can delete.

    Raised before anything is deleted, so a refusal leaves the plugin and everything
    under it exactly as it was.
    """

    def __init__(self, plugin_name: str, reason: str) -> None:
        """Name the plugin and why it was refused — both reach the user."""
        super().__init__(f"Plugin '{plugin_name}' could not be deleted: {reason}.")


class InputRejectedError(CoreError):
    """A handler refused what the user sent. The message says what to do about it."""

    pass


class ScopePinnedError(CoreError):
    """A conversation pinned to one field was asked to be pinned to another.

    A pin is what lets a thread be trusted to stay in its field, so it is set once and
    never moved: a second field is a second conversation.
    """

    def __init__(self, pinned: str) -> None:
        """Name the scope the conversation is already in, which is the way out."""
        super().__init__(
            f"This conversation is pinned to {pinned}. Start a new one for another "
            f"field."
        )


class ConfigurationError(CoreError):
    """A setting is missing or unusable, so the app cannot be assembled."""

    pass


class AdapterError(CoreError):
    """Something outside cora failed. The class is the category, not a diagnosis.

    Every adapter translates its technology's exceptions into one of these, so nothing
    from a library reaches a shell — and the original is kept as the cause for the log.
    """

    message: str

    def __init__(self) -> None:
        """Take no message.

        The class is the message, so one category reads alike everywhere it is raised.
        """
        super().__init__(self.message)


class EmbeddingError(AdapterError):
    """The embedding model could not be loaded or could not run."""

    message = "Could not generate embeddings for the document. Please try again."


class RetrievalError(AdapterError):
    """The index could not be reached, read or written."""

    message = "The knowledge base is temporarily unavailable. Please try again."


class LlmError(AdapterError):
    """The model gave cora nothing it could use. The subclasses say what went wrong."""

    message = "The assistant is temporarily unavailable. Please try again."


class LlmTimeoutError(LlmError):
    """The provider did not answer inside the request timeout."""

    message = "The assistant took too long to answer. Please try again."


class LlmBusyError(LlmError):
    """The provider is rate-limiting; the same question may work in a moment."""

    message = "The assistant is busy right now. Please try again in a moment."


class LlmKeyRejectedError(LlmError):
    """The provider rejected the key. No retry helps, so the message says so."""

    message = (
        "The assistant's API key was rejected. Check OPENROUTER_API_KEY and restart."
    )


class LlmConversationTooLongError(LlmError):
    """The prompt is past the model's context window — the thread, not the question."""

    message = (
        "This conversation has grown too long for the assistant to read. Please start "
        "a new one."
    )


class LlmTruncatedError(LlmError):
    """The answer stopped at the output limit, so half a sentence arrived.

    A failure rather than a short answer: serving it would present an unfinished
    sentence as the answer.
    """

    message = (
        "The answer was cut off before it finished. Please try again, or ask for a "
        "shorter answer."
    )


class LlmEmptyReplyError(LlmError):
    """The round asked for no tool and wrote nothing — a turn with no answer in it."""

    message = "The assistant sent an empty answer. Please try again."


class LlmMalformedToolCallError(LlmError):
    """A tool call whose arguments never parsed, so the round asked for nothing.

    Its own category because the model's prose beside it reads as a final answer, and
    serving that is an answer resting on work that was never done.
    """

    message = "The assistant garbled what it was trying to do. Please try again."


class MemoryStoreError(AdapterError):
    """What cora remembers about the user could not be read or written."""

    message = "What I remember about you is temporarily unavailable. Please try again."


class DocumentStoreError(AdapterError):
    """A document's kept text could not be read or written, so no span can be opened."""

    message = "That document is temporarily unavailable. Please try again."


class ConversationStoreError(AdapterError):
    """The record of earlier conversations could not be read or written."""

    message = "I could not reach your earlier conversations. Please try again."


class OutputStoreError(AdapterError):
    """What an effect produced could not be written."""

    message = "I could not write that file. Nothing else in this conversation changed."


class GraphRunError(AdapterError):
    """A turn came back with no answer: the walk took no step, or settled nothing.

    Either way there is nothing to report, and a blank answer would read like a
    successful turn — and be recorded as one.
    """

    message = "The assistant could not answer that. Please try again."


class NothingToResumeError(CoreError):
    """A decision was answered for a thread that is not waiting on one.

    A card clicked twice, or one left open while the conversation moved on.
    """

    def __init__(self) -> None:
        """Say so in one sentence: the thread is still answerable afterwards."""
        super().__init__("There is nothing waiting on your decision.")


class ToolLoopLimitError(CoreError):
    """The turn spent its tool rounds without reaching an answer.

    The budget is what keeps a model that keeps searching from running a turn
    indefinitely; the question is worth rephrasing rather than repeating.
    """

    def __init__(self) -> None:
        """Ask for a rephrasing: repeating the question would spend the budget again."""
        super().__init__(
            "Sorry, I couldn't complete your request. Please try rephrasing."
        )
