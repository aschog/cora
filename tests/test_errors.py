from docchat.errors import DocChatError


def test_base_error_exposes_user_presentable_message() -> None:
    error = DocChatError("Something went wrong. Please try again.")

    assert error.user_message == "Something went wrong. Please try again."
