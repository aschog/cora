import itertools
import json

import httpx
import pytest

from cora.frontends.telegram.api import (
    AFTER_A_DROP,
    LONGEST_WAIT,
    MOST_WAITS,
    BotApi,
    Message,
)

TOKEN = "a-token"


def _updates(*batches: list[dict]) -> tuple[httpx.MockTransport, list[dict]]:
    # Answers each poll with the next batch and then nothing, and hands back the calls
    # it was asked for, in the order they came.
    asked: list[dict] = []
    batched = iter(batches)

    def answer(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        asked.append({"method": request.url.path.rsplit("/", 1)[-1], **payload})
        if request.url.path.endswith("getUpdates"):
            return httpx.Response(200, json={"ok": True, "result": next(batched, [])})
        return httpx.Response(200, json={"ok": True, "result": {}})

    return httpx.MockTransport(answer), asked


def _bot(transport: httpx.MockTransport) -> BotApi:
    return BotApi(TOKEN, client=httpx.Client(transport=transport))


def _text(update_id: int, chat: int, text: str) -> dict:
    return {"update_id": update_id, "message": {"chat": {"id": chat}, "text": text}}


def test_a_text_message_arrives_as_the_chat_and_the_text_it_carried() -> None:
    transport, _ = _updates([_text(1, 11, "hello")])

    [first] = itertools.islice(_bot(transport).messages(), 1)

    assert first == Message(chat=11, text="hello")


def test_an_update_carrying_no_text_is_skipped_rather_than_answered() -> None:
    transport, _ = _updates(
        [
            {"update_id": 1, "message": {"chat": {"id": 11}, "sticker": {}}},
            {"update_id": 2, "edited_message": {"chat": {"id": 11}, "text": "oops"}},
            _text(3, 11, "hello"),
        ]
    )

    [first] = itertools.islice(_bot(transport).messages(), 1)

    assert first == Message(chat=11, text="hello")


def test_an_update_is_acknowledged_so_it_is_never_read_twice() -> None:
    transport, asked = _updates(
        [{"update_id": 7, "message": {"chat": {"id": 11}, "sticker": {}}}],
        [_text(8, 11, "hello")],
    )

    list(itertools.islice(_bot(transport).messages(), 1))

    polls = [call for call in asked if call["method"] == "getUpdates"]
    assert [poll["offset"] for poll in polls] == [0, 8]


def test_a_poll_that_drops_is_waited_out_and_asked_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    polls = iter([httpx.ConnectTimeout("dropped"), None])

    def answer(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("getUpdates") and (dropped := next(polls, None)):
            raise dropped
        return httpx.Response(200, json={"ok": True, "result": [_text(1, 11, "hi")]})

    [first] = itertools.islice(_bot(httpx.MockTransport(answer)).messages(), 1)

    assert first == Message(chat=11, text="hi")
    assert waited


def test_an_answer_is_sent_to_the_chat_it_was_asked_in() -> None:
    transport, asked = _updates()

    _bot(transport).send(11, "Sleep, not volume.")

    assert asked == [
        {"method": "sendMessage", "chat_id": 11, "text": "Sleep, not volume."}
    ]


def test_a_refused_call_is_not_swallowed() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

    with pytest.raises(httpx.HTTPStatusError):
        list(itertools.islice(_bot(httpx.MockTransport(refuse)).messages(), 1))


def test_the_token_is_not_in_what_a_refused_call_raises() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"ok": False, "description": "Unauthorized"})

    with pytest.raises(httpx.HTTPStatusError) as refused:
        list(itertools.islice(_bot(httpx.MockTransport(refuse)).messages(), 1))

    assert TOKEN not in str(refused.value)
    assert "401" in str(refused.value)


def test_a_chat_that_blocked_the_bot_does_not_end_the_bot() -> None:
    def blocked(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403, json={"ok": False, "description": "Forbidden: bot was blocked"}
        )

    _bot(httpx.MockTransport(blocked)).send(11, "hello")


def test_a_send_refused_for_any_other_reason_is_raised() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"ok": False, "description": "Bad Request"})

    with pytest.raises(httpx.HTTPStatusError):
        _bot(httpx.MockTransport(refuse)).send(11, "hello")


def test_nothing_is_sent_for_nothing_to_say() -> None:
    transport, asked = _updates()

    _bot(transport).send(11, "")

    assert asked == []


def test_being_asked_to_wait_is_waited_out_and_the_call_made_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    calls: list[httpx.Request] = []

    def busy(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                429,
                json={"ok": False, "parameters": {"retry_after": 7}},
            )
        return httpx.Response(200, json={"ok": True, "result": {}})

    _bot(httpx.MockTransport(busy)).send(11, "hello")

    assert waited == [7.0]
    assert len(calls) == 2


def test_the_poll_is_read_for_longer_than_the_poll_is_held_open() -> None:
    from cora.frontends.telegram.api import PATIENCE, POLL_SECONDS

    waits = PATIENCE.as_dict()
    read, connect = waits["read"] or 0.0, waits["connect"] or 0.0

    assert read > POLL_SECONDS, (
        "a client that reads for less than the poll is held open drops every quiet "
        "half-minute and asks again"
    )
    assert connect < read, "a host that is not there should be found out in seconds"


def test_only_the_updates_the_bot_answers_are_asked_for() -> None:
    transport, asked = _updates([_text(1, 11, "hello")])

    list(itertools.islice(_bot(transport).messages(), 1))

    assert asked[0]["allowed_updates"] == ["message"]


def test_a_reply_whose_connection_drops_does_not_end_the_bot() -> None:
    """The poll has a net for a dropped connection and the reply had none — one Wi-Fi
    hop between the poll and the answer took the whole bot down."""

    def dropped(request: httpx.Request) -> httpx.Response:
        raise httpx.RemoteProtocolError("Server disconnected without a response.")

    _bot(httpx.MockTransport(dropped)).send(11, "hello")


def test_a_rate_that_outlasts_one_wait_is_waited_out_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    calls: list[httpx.Request] = []

    def busy(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) <= 2:
            return httpx.Response(
                429, json={"ok": False, "parameters": {"retry_after": 1}}
            )
        return httpx.Response(200, json={"ok": True, "result": {}})

    _bot(httpx.MockTransport(busy)).send(11, "hello")

    assert waited == [1.0, 1.0]
    assert len(calls) == 3


def test_a_rate_that_outlasts_every_wait_still_does_not_end_the_bot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The poll is the one call no rate may end: every wait spent and still refused, it
    is waited out once more and asked again, not raised at the loop."""
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    polls = itertools.count(1)

    def busy(request: httpx.Request) -> httpx.Response:
        if next(polls) <= MOST_WAITS + 1:
            return httpx.Response(
                429, json={"ok": False, "parameters": {"retry_after": 1}}
            )
        return httpx.Response(200, json={"ok": True, "result": [_text(1, 11, "hello")]})

    [first] = itertools.islice(_bot(httpx.MockTransport(busy)).messages(), 1)

    assert first == Message(chat=11, text="hello")
    assert waited == [1.0] * MOST_WAITS + [AFTER_A_DROP]


def test_a_wait_longer_than_the_ceiling_is_capped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A flood wait of an hour would park the bot for an hour without a word."""
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    calls: list[httpx.Request] = []

    def busy(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(
                429, json={"ok": False, "parameters": {"retry_after": 3600}}
            )
        return httpx.Response(200, json={"ok": True, "result": {}})

    _bot(httpx.MockTransport(busy)).send(11, "hello")

    assert waited == [LONGEST_WAIT]


def test_a_wait_asked_for_in_something_other_than_json_is_still_waited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 429 from something between here and Telegram is a page, not a body with a
    number in it, and reading it as one crashed before the wait."""
    waited: list[float] = []
    monkeypatch.setattr("cora.frontends.telegram.api.time.sleep", waited.append)
    calls: list[httpx.Request] = []

    def busy(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, text="<html>429 Too Many Requests</html>")
        return httpx.Response(200, json={"ok": True, "result": {}})

    _bot(httpx.MockTransport(busy)).send(11, "hello")

    assert waited == [AFTER_A_DROP]
    assert len(calls) == 2
