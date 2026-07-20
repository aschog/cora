"""Application-wide error hierarchy.

Every error carries a user-presentable message; the UI shell renders it
verbatim, so no failure ever reaches the user as a stack trace.
"""


class DocChatError(Exception):
    """Base error for all application failures."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message
