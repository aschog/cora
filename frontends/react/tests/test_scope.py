from pathlib import Path
from typing import Any

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.frontends.react.api import NO_SUCH_SCOPE, api
from cora.ports.chat_model import ModelReply
from cora.ports.host import DEFAULT_SCOPE, Extension, Host
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
    with TestClient(api(_served())) as reader:
        offered = reader.get("/api/scopes").json()

    assert offered == {"available": list(BOTH), "default": DEFAULT_SCOPE, "pages": {}}


def test_a_field_with_a_page_is_offered_with_the_path_it_is_served_under(
    tmp_path: Path,
) -> None:

    def extend(cora: Host) -> None:
        cora.register_instructions("Coach.", scope="fitness")
        cora.register_page(tmp_path, scope="fitness")

    app = assembled(
        plugins=(
            Extension(module="fixture_plugins.coaching", extend=extend),
            make_plugin(name="trips", tools=(make_tool("route_to"),), scope="travel"),
        ),
        scopes=BOTH,
    )

    with TestClient(api(app)) as reader:
        offered = reader.get("/api/scopes").json()

    assert offered == {
        "available": list(BOTH),
        "default": DEFAULT_SCOPE,
        "pages": {"fitness": "/pages/fitness/"},
    }


def test_a_second_field_on_a_pinned_thread_is_refused_as_a_sentence() -> None:
    app = _served(ModelReply(text="Protein, then."), ModelReply(text="never said"))

    with TestClient(api(app)) as reader:
        _asked(reader, question="How much protein?", pin="fitness")
        streamed = _asked(reader, question="Sleeper?", pin="travel")

    [(name, data)] = streamed
    assert name == "error"
    assert "fitness" in data["error"]


def test_a_field_the_deployment_does_not_run_is_refused_before_the_turn() -> None:
    with TestClient(api(_served())) as reader:
        refused = reader.post(
            "/api/ask",
            json={"thread_id": THREAD, "question": "Anything?", "pin": "cooking"},
        )

    assert refused.status_code == 400
    assert refused.json()["error"] == NO_SUCH_SCOPE


def test_a_listed_conversation_says_which_field_it_is_fixed_to() -> None:
    app = _served(
        ModelReply(text="Protein, then."),
        # The second conversation is pinned to nothing, so it is routed before it is
        # answered — one reading, then the answer.
        ModelReply(text=DEFAULT_SCOPE),
        ModelReply(text="Anything."),
    )

    with TestClient(api(app)) as reader:
        _asked(reader, question="How much protein?", pin="fitness")
        _asked(reader, question="Anything else?", thread_id="t2")
        listed = reader.get("/api/conversations").json()

    fixed = {each["opened_with"]: each["pin"] for each in listed}
    assert fixed == {"How much protein?": "fitness", "Anything else?": None}
