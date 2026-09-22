import hashlib
import pathlib
from collections.abc import Iterator
from dataclasses import replace

from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Turn
from cora.domain.errors import (
    ConversationStoreError,
)
from cora.frontends.react.api import (
    MAX_REQUEST_BYTES,
    NO_LENGTH,
    NO_SUCH_DOCUMENT,
    OVER_CEILING,
    UNKEPT,
    api,
)
from cora.ports.host import DEFAULT_SCOPE, Extension, Host
from fakes import (
    FailingConversations,
    FakeConversations,
    FakeMemory,
)
from fixture_plugins import make_plugin, make_tool

NOTES = b"Squats stall on sleep, not on volume. The block holds intensity."


def client(app: App, *, ui: pathlib.Path | None = None) -> TestClient:
    return TestClient(api(app, ui=ui))


def test_an_upload_is_ingested_and_reports_the_chunks_it_cut() -> None:
    app = assembled()

    added = client(app).post(
        "/api/documents", files={"file": ("notes.md", NOTES, "text/markdown")}
    )

    assert added.status_code == 200
    assert added.json() == {"document": "notes.md", "chunks": 1, "scope": DEFAULT_SCOPE}
    assert app.knowledge_base.list_sources() == ["notes.md"]


def test_a_passage_reads_back_from_the_upload_its_span_was_measured_in() -> None:
    app = indexed(assembled(), ("notes.md", NOTES))
    upload = hashlib.sha256(NOTES).hexdigest()

    kept = client(app).get(f"/api/uploads/{DEFAULT_SCOPE}/{upload}")

    assert kept.status_code == 200
    assert kept.json()["text"] == NOTES.decode()


def test_a_citation_into_a_deleted_document_says_the_document_is_gone() -> None:
    app = assembled()
    client = _scoped(app)
    client.post(
        "/api/documents",
        files={"file": ("kyoto.md", KYOTO, "text/markdown")},
        data={"scope": TRAVEL},
    )
    upload = hashlib.sha256(KYOTO).hexdigest()
    assert client.get(f"/api/uploads/{TRAVEL}/{upload}").status_code == 200

    assert client.delete(f"/api/documents/{TRAVEL}/kyoto.md").status_code == 204

    opened = client.get(f"/api/uploads/{TRAVEL}/{upload}")
    assert opened.status_code == 404
    assert opened.json()["error"] == UNKEPT


def test_the_memory_endpoint_lists_the_facts_oldest_first() -> None:
    app = assembled(memory=FakeMemory(("No burpees.", "Four sessions a week.")))

    facts = client(app).get("/api/memory")

    assert [fact["text"] for fact in facts.json()] == [
        "No burpees.",
        "Four sessions a week.",
    ]


def test_a_fact_is_forgotten_by_its_key_and_the_lot_by_none() -> None:
    memory = FakeMemory(("No burpees.", "Four sessions a week."))
    with client(assembled(memory=memory)) as reader:
        forgotten = reader.delete("/api/memory/f1")

        assert forgotten.status_code == 204
        assert [fact.text for fact in memory.recall()] == ["Four sessions a week."]

        cleared = reader.delete("/api/memory")

    assert cleared.status_code == 204
    assert memory.recall() == ()


def test_a_conversation_is_deleted_by_its_thread_and_leaves_the_listing() -> None:
    conversations = FakeConversations()
    conversations.record("t1", Turn(question="First?", result=ChatResult(answer="a")))
    conversations.record("t2", Turn(question="Second?", result=ChatResult(answer="b")))
    with client(assembled(conversations=conversations)) as reader:
        deleted = reader.delete("/api/conversations/t2")

        assert deleted.status_code == 204
        assert [
            session["thread_id"] for session in reader.get("/api/conversations").json()
        ] == ["t1"]
        assert reader.get("/api/conversations/t2").json() == []


def test_a_conversation_store_that_cannot_be_read_reports_its_own_message() -> None:
    app = assembled(conversations=FailingConversations())

    failed = client(app).get("/api/conversations")

    assert failed.status_code == 503
    assert failed.json()["error"] == ConversationStoreError().user_message


def test_the_plugins_endpoint_carries_what_each_plugin_registered() -> None:
    app = assembled(plugin=make_plugin("birds", tools=(make_tool("count"),), scope="b"))

    listed = client(app).get("/api/plugins").json()

    assert listed == [
        {
            "name": "birds",
            "source": "fixture_plugins.birds",
            "scopes": ["b"],
            "deletable": False,
            "going": ["b"],
            "contributions": [
                {"kind": "instructions", "name": "", "scope": "b", "note": ""},
                {"kind": "tool", "name": "count", "scope": "b", "note": ""},
            ],
        }
    ]


def test_an_upload_over_the_ceiling_is_refused_before_the_body_is_parsed() -> None:
    app = assembled()

    refused = client(app).post(
        "/api/documents",
        content=b"x" * (MAX_REQUEST_BYTES + 1),
        headers={"content-type": "multipart/form-data; boundary=nope"},
    )

    assert refused.status_code == 413
    assert refused.json()["error"] == OVER_CEILING
    assert app.knowledge_base.list_sources() == []


FITNESS, TRAVEL = "fitness", "travel"
KYOTO = b"The sleeper to Kyoto sells out a month before the maples turn."


def _scoped(app: App) -> TestClient:
    return TestClient(api(replace(app, scopes=(FITNESS, TRAVEL))))


def test_an_upload_lands_in_the_field_it_names() -> None:
    app = assembled()
    client = _scoped(app)

    client.post(
        "/api/documents",
        files={"file": ("kyoto.md", KYOTO, "text/markdown")},
        data={"scope": TRAVEL},
    )

    assert app.knowledge_base.list_sources(TRAVEL) == ["kyoto.md"]
    assert app.knowledge_base.list_sources(FITNESS) == []


def test_a_document_is_deleted_by_its_name_and_leaves_the_listing() -> None:
    app = assembled()
    client = _scoped(app)
    for name, data in (("kyoto.md", KYOTO), ("notes.md", NOTES)):
        client.post(
            "/api/documents",
            files={"file": (name, data, "text/markdown")},
            data={"scope": TRAVEL},
        )

    deleted = client.delete(f"/api/documents/{TRAVEL}/kyoto.md")

    assert deleted.status_code == 204
    assert client.get(f"/api/documents?scope={TRAVEL}").json() == ["notes.md"]
    upload = hashlib.sha256(KYOTO).hexdigest()
    assert client.get(f"/api/uploads/{TRAVEL}/{upload}").status_code == 404


def test_a_document_is_read_back_by_its_name_every_upload_oldest_first() -> None:
    app = assembled()
    client = _scoped(app)
    for data in (b"# Deadlift 14 kg\n3 sets of 10", b"# Swing 14 kg\n2 sets of 10"):
        client.post(
            "/api/documents",
            files={"file": ("2026-09-18.md", data, "text/markdown")},
            data={"scope": FITNESS},
        )

    read = client.get(f"/api/documents/{FITNESS}/2026-09-18.md")

    assert read.status_code == 200
    assert [each["text"] for each in read.json()] == [
        "# Deadlift 14 kg\n3 sets of 10",
        "# Swing 14 kg\n2 sets of 10",
    ]


def test_a_name_nothing_was_uploaded_under_reads_as_not_there() -> None:
    app = assembled()
    client = _scoped(app)

    read = client.get(f"/api/documents/{FITNESS}/never.md")

    assert read.status_code == 404
    assert read.json() == {"error": NO_SUCH_DOCUMENT}


def test_reading_a_document_of_a_field_nobody_loaded_is_refused() -> None:
    client = _scoped(assembled())

    refused = client.get("/api/documents/atlantis/never.md")

    assert refused.status_code == 400
    assert "atlantis" in refused.json()["error"]
    assert FITNESS in refused.json()["error"]


def test_a_refusal_quotes_back_only_so_much_of_the_name_it_was_given() -> None:
    refused = _scoped(assembled()).get(f"/api/documents?scope={'z' * 5000}")

    assert refused.status_code == 400
    assert len(refused.json()["error"]) < 200


def test_an_upload_that_does_not_say_how_large_it_is_is_refused() -> None:
    app = assembled()

    def chunked() -> Iterator[bytes]:
        yield b"x"

    refused = client(app).post(
        "/api/documents",
        content=chunked(),
        headers={"content-type": "multipart/form-data; boundary=nope"},
    )

    assert refused.status_code == 411
    assert refused.json()["error"] == NO_LENGTH
    assert app.knowledge_base.list_sources() == []


def test_the_plugins_endpoint_carries_a_page_among_the_contributions(
    tmp_path: pathlib.Path,
) -> None:

    def extend(cora: Host) -> None:
        cora.register_page(tmp_path, scope="b")

    app = assembled(plugin=Extension(module="fixture_plugins.birds", extend=extend))

    [listed] = client(app).get("/api/plugins").json()

    assert listed["contributions"] == [
        {"kind": "page", "name": "", "scope": "b", "note": ""}
    ]


def test_a_pin_that_cannot_be_read_costs_its_row_and_not_the_listing() -> None:
    # The pin is which field a conversation belongs to, read off its checkpoint. The
    # listing is how a reader reaches any conversation at all, so one checkpoint that
    # will not open must not take the rail down with it.
    conversations = FakeConversations()
    conversations.record("t1", Turn(question="First?", result=ChatResult(answer="a")))
    app = assembled(conversations=conversations)
    broken = replace(app, agent=_NoPin(app.agent))

    listed = client(broken).get("/api/conversations")

    assert listed.status_code == 200
    assert [session["thread_id"] for session in listed.json()] == ["t1"]
    assert listed.json()[0]["pin"] is None


class _NoPin:
    def __init__(self, agent: object) -> None:
        self._agent = agent

    def __getattr__(self, name: str) -> object:
        return getattr(self._agent, name)

    def pinned(self, thread_id: str) -> str | None:
        raise RuntimeError("that checkpoint will not open")
