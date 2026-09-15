import logging

import pytest

from cora.domain.errors import ConfigurationError
from cora.frontends.telegram.server import (
    CHATS,
    HTTP_LOGGER,
    TOKEN,
    allowed,
    serve,
    token,
)


def test_a_deployment_naming_no_chat_refuses_to_start(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(TOKEN, "a-token")
    monkeypatch.delenv(CHATS, raising=False)

    with pytest.raises(SystemExit) as refused:
        serve()

    assert refused.value.code == 1
    assert CHATS in capsys.readouterr().err


def test_a_deployment_holding_no_token_refuses_to_start(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(CHATS, "11")
    monkeypatch.delenv(TOKEN, raising=False)

    with pytest.raises(SystemExit) as refused:
        serve()

    assert refused.value.code == 1
    assert TOKEN in capsys.readouterr().err


def test_the_chats_are_read_as_the_ids_they_are() -> None:
    assert allowed({CHATS: "11, -1001234567890 ,22"}) == (11, -1001234567890, 22)


def test_a_chat_that_is_not_an_id_refuses_rather_than_answering_nobody() -> None:
    with pytest.raises(ConfigurationError, match=CHATS):
        allowed({CHATS: "11,@my_channel"})


def test_a_blank_token_is_no_token() -> None:
    with pytest.raises(ConfigurationError, match=TOKEN):
        token({TOKEN: "   "})


def test_the_client_that_carries_the_token_in_its_urls_does_not_log_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """httpx writes one INFO line per request, and the URL it writes holds the token.
    Nothing raises that logger today, which is a defence one `basicConfig` deep."""
    monkeypatch.setattr(
        logging.getLogger(HTTP_LOGGER), "level", logging.NOTSET, raising=False
    )
    monkeypatch.delenv(TOKEN, raising=False)
    monkeypatch.delenv(CHATS, raising=False)

    with pytest.raises(SystemExit):
        serve()

    assert logging.getLogger(HTTP_LOGGER).level == logging.WARNING
