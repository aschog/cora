"""The scope, as the page reaches it: what the deployment offers, what a thread is
pinned to, and the pin travelling in beside a question."""

from typing import Any

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.frontends.react.api import NO_SUCH_SCOPE, api
from cora.ports.chat_model import ModelReply
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeConversations, ScriptedChatModel
from fixture_plugins import make_plugin, make_tool
from sse import frames

THREAD = "t1"
BOTH = ("fitness", "travel")


def _served(*replies: ModelReply) -> App:
    return assembled(
        chat_model=ScriptedChatModel(list(replies) or [ModelReply(text="ok")]),
        conversations=FakeConversations(),
        plugins=(
            make_plugin(name="coaching", tools=(make_tool("bmi"),), scope="fitness"),
            make_plugin(name="trips", tools=(make_tool("route_to"),), scope="travel"),
        ),
        scopes=BOTH,
    )


def _asked(reader: TestClient, **body: Any) -> list[tuple[str, dict]]:
    streamed = reader.post("/api/ask", json={"thread_id": THREAD, **body})
    assert streamed.status_code == 200
    return frames(streamed.text)


def test_the_page_is_told_which_fields_the_deployment_offers() -> None:
    """The picker is drawn from this: a deployment with one field has nothing to pick,
    and the default is what a question belonging to no field is answered in."""
    with TestClient(api(_served(), scopes=BOTH)) as reader:
        offered = reader.get("/api/scopes").json()

    assert offered == {"available": list(BOTH), "default": DEFAULT_SCOPE}


def test_a_question_can_carry_the_pin_that_fixes_the_thread_to_a_field() -> None:
    """The pin is a key of the thread's own state, so it needs a turn to be written —
    and a page that reloads reads it back off the thread rather than off its own."""
    app = _served(ModelReply(text="Protein, then."))

    with TestClient(api(app, scopes=BOTH)) as reader:
        assert reader.get(f"/api/sessions/{THREAD}/scope").json() == {"pin": None}

        streamed = _asked(reader, question="How much protein?", pin="fitness")

        assert streamed[-1][0] == "turn"
        assert reader.get(f"/api/sessions/{THREAD}/scope").json() == {"pin": "fitness"}


def test_a_second_field_on_a_pinned_thread_is_refused_as_a_sentence() -> None:
    """The rule is the engine's, so it arrives the way a screening refusal does: on the
    stream, as the error that ends it. The reader is told which field the conversation
    is in, which is what tells them to start another."""
    app = _served(ModelReply(text="Protein, then."), ModelReply(text="never said"))

    with TestClient(api(app, scopes=BOTH)) as reader:
        _asked(reader, question="How much protein?", pin="fitness")
        streamed = _asked(reader, question="Sleeper?", pin="travel")

    [(name, data)] = streamed
    assert name == "error"
    assert "fitness" in data["error"]


def test_a_field_the_deployment_does_not_run_is_refused_before_the_turn() -> None:
    """A pin cannot be undone, so a pin to a field no registration is under would leave
    the thread answering plainly for ever. Refused where what is offered is known."""
    with TestClient(api(_served(), scopes=BOTH)) as reader:
        refused = reader.post(
            "/api/ask",
            json={"thread_id": THREAD, "question": "Anything?", "pin": "cooking"},
        )

    assert refused.status_code == 400
    assert refused.json()["error"] == NO_SUCH_SCOPE
