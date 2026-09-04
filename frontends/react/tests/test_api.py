import hashlib
import pathlib
from collections.abc import Iterator
from typing import Any

import anyio
import httpx
import pytest
from python_multipart.exceptions import (
    DecodeError,
    MultipartParseError,
    QuerystringParseError,
)
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.domain.chat_result import ChatResult
from cora.domain.conversation import Turn
from cora.domain.errors import ConversationStoreError, MemoryStoreError
from cora.engine.ingestion import DEFAULT_MAX_BYTES
from cora.frontends.react.api import (
    MAX_REQUEST_BYTES,
    NO_LENGTH,
    OVER_CEILING,
    REFUSALS,
    UNREADABLE_UPLOAD,
    api,
)
from cora.ports.host import DEFAULT_SCOPE
from fakes import FailingConversations, FailingMemory, FakeConversations, FakeMemory
from fixture_plugins import make_plugin, make_tool

NOTES = b"Squats stall on sleep, not on volume. The block holds intensity."


def client(app: App, *, ui: pathlib.Path | None = None) -> TestClient:
    return TestClient(api(app, ui=ui))


def test_the_documents_endpoint_lists_what_is_indexed() -> None:
    app = indexed(assembled(), ("notes.md", NOTES))

    listed = client(app).get("/api/documents")

    assert listed.status_code == 200
    assert listed.json() == ["notes.md"]


def test_an_upload_is_ingested_and_reports_the_chunks_it_cut() -> None:
    app = assembled()

    added = client(app).post(
        "/api/documents", files={"file": ("notes.md", NOTES, "text/markdown")}
    )

    assert added.status_code == 200
    assert added.json() == {"document": "notes.md", "chunks": 1, "scope": DEFAULT_SCOPE}
    assert app.knowledge_base.list_sources() == ["notes.md"]


def test_a_file_already_indexed_reports_no_chunks_rather_than_failing() -> None:
    app = assembled()
    upload = {"file": ("notes.md", NOTES, "text/markdown")}
    with client(app) as reader:
        reader.post("/api/documents", files=upload)

        again = reader.post("/api/documents", files=upload)

    assert again.status_code == 200
    assert again.json()["chunks"] == 0


def test_an_upload_that_cannot_be_ingested_says_so_and_indexes_nothing() -> None:
    """The message the user reads is the error's own, never a traceback."""
    app = assembled()

    refused = client(app).post(
        "/api/documents", files={"file": ("empty.txt", b"   ", "text/plain")}
    )

    assert refused.status_code == 400
    assert "empty.txt" in refused.json()["error"]
    assert app.knowledge_base.list_sources() == []


def test_a_passage_reads_back_from_the_upload_its_span_was_measured_in() -> None:
    app = indexed(assembled(), ("notes.md", NOTES))
    upload = hashlib.sha256(NOTES).hexdigest()

    kept = client(app).get(f"/api/uploads/{DEFAULT_SCOPE}/{upload}")

    assert kept.status_code == 200
    assert kept.json()["text"] == NOTES.decode()


def test_an_upload_never_kept_says_so_rather_than_serving_an_empty_document() -> None:
    missing = client(assembled()).get(
        f"/api/uploads/{DEFAULT_SCOPE}/nothingwaskeptunderthis"
    )

    assert missing.status_code == 404


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


def test_a_memory_store_that_cannot_be_read_reports_its_own_message() -> None:
    app = assembled(memory=FailingMemory(MemoryStoreError()))

    failed = client(app).get("/api/memory")

    assert failed.status_code == 503
    assert failed.json()["error"] == MemoryStoreError().user_message


def test_the_sessions_endpoint_lists_the_conversations_newest_first() -> None:
    conversations = FakeConversations()
    conversations.record("t1", Turn(question="First?", result=ChatResult(answer="a")))
    conversations.record("t2", Turn(question="Second?", result=ChatResult(answer="b")))
    app = assembled(conversations=conversations)

    listed = client(app).get("/api/sessions")

    assert [session["opened_with"] for session in listed.json()] == [
        "Second?",
        "First?",
    ]


def test_a_session_returns_its_turns_oldest_first() -> None:
    conversations = FakeConversations()
    conversations.record("t1", Turn(question="First?", result=ChatResult(answer="a")))
    conversations.record("t1", Turn(question="Then?", result=ChatResult(answer="b")))
    app = assembled(conversations=conversations)

    turns = client(app).get("/api/sessions/t1")

    assert [turn["question"] for turn in turns.json()] == ["First?", "Then?"]


def test_a_thread_never_recorded_is_empty_rather_than_missing() -> None:
    """An unopened conversation has no turns; it is not a page that does not exist."""
    app = assembled(conversations=FakeConversations())

    turns = client(app).get("/api/sessions/never-spoke")

    assert turns.status_code == 200
    assert turns.json() == []


def test_a_conversation_is_deleted_by_its_thread_and_leaves_the_listing() -> None:
    conversations = FakeConversations()
    conversations.record("t1", Turn(question="First?", result=ChatResult(answer="a")))
    conversations.record("t2", Turn(question="Second?", result=ChatResult(answer="b")))
    with client(assembled(conversations=conversations)) as reader:
        deleted = reader.delete("/api/sessions/t2")

        assert deleted.status_code == 204
        assert [
            session["thread_id"] for session in reader.get("/api/sessions").json()
        ] == ["t1"]
        assert reader.get("/api/sessions/t2").json() == []


def test_deleting_a_conversation_a_store_cannot_reach_reports_its_own_message() -> None:
    app = assembled(conversations=FailingConversations())

    failed = client(app).delete("/api/sessions/t1")

    assert failed.status_code == 503
    assert failed.json()["error"] == ConversationStoreError().user_message


def test_deleting_a_conversation_with_no_store_behind_it_is_done() -> None:
    """The reading the panels take: a deployment with no place to record turns has
    nothing to delete, which is a request already satisfied."""
    deleted = client(assembled()).delete("/api/sessions/t1")

    assert deleted.status_code == 204


def test_a_conversation_store_that_cannot_be_read_reports_its_own_message() -> None:
    app = assembled(conversations=FailingConversations())

    failed = client(app).get("/api/sessions")

    assert failed.status_code == 503
    assert failed.json()["error"] == ConversationStoreError().user_message


@pytest.mark.parametrize("path", ["/api/memory", "/api/sessions"])
def test_a_panel_with_no_store_behind_it_is_empty_rather_than_broken(path: str) -> None:
    """cora assembles without a memory slot or a conversation store; the panels those
    fill are then empty, and nothing else on the page notices."""
    answered = client(assembled()).get(path)

    assert answered.status_code == 200
    assert answered.json() == []


@pytest.mark.parametrize("path", ["/api/memory", "/api/memory/f1"])
def test_forgetting_where_nothing_is_kept_is_done_rather_than_missing(
    path: str,
) -> None:
    """The same contract the panels read by: a deployment with no memory slot has
    nothing to forget, which is a request already satisfied — not a page that is not
    there."""
    forgotten = client(assembled()).delete(path)

    assert forgotten.status_code == 204


def test_the_plugins_endpoint_carries_what_each_plugin_registered() -> None:
    """The listing `make plugins` prints, as the menu reads it — one projection of the
    registrations, so a terminal and the page cannot disagree."""
    app = assembled(plugin=make_plugin("birds", tools=(make_tool("count"),), scope="b"))

    listed = client(app).get("/api/plugins").json()

    assert listed == [
        {
            "name": "birds",
            "source": "fixture_plugins.birds",
            "scopes": ["b"],
            "contributions": [
                {"kind": "instructions", "name": "", "scope": "b", "note": ""},
                {"kind": "tool", "name": "count", "scope": "b", "note": ""},
            ],
        }
    ]


def test_with_no_plugin_configured_the_page_is_told_bare_cora() -> None:
    assert client(assembled(plugins=())).get("/api/plugins").json() == []


def test_a_built_page_is_served_beside_the_api(tmp_path: pathlib.Path) -> None:
    """One process is the whole app: the API answers under `/api`, the build under
    everything else."""
    (tmp_path / "index.html").write_text("<!doctype html><title>cora</title>")

    with client(assembled(), ui=tmp_path) as reader:
        assert "<title>cora</title>" in reader.get("/").text
        assert reader.get("/api/documents").status_code == 200


def test_with_no_build_present_the_api_still_answers(tmp_path: pathlib.Path) -> None:
    """A dev machine runs the page on Vite; a missing build is not a broken server."""
    with client(assembled(), ui=tmp_path / "never-built") as reader:
        assert reader.get("/api/documents").status_code == 200
        assert reader.get("/").status_code == 404


def test_an_upload_over_the_ceiling_is_refused_before_the_body_is_parsed() -> None:
    """The multipart parser spools a file part to a temporary file with no ceiling of
    its own, and `ingest` measures the document only once the whole part has been read
    into memory — so a 2 GB part fills the temp dir and then RAM before anything says
    no. The body here is not multipart at all: only a guard that fires before the parse
    can answer it."""
    app = assembled()

    refused = client(app).post(
        "/api/documents",
        content=b"x" * (MAX_REQUEST_BYTES + 1),
        headers={"content-type": "multipart/form-data; boundary=nope"},
    )

    assert refused.status_code == 413
    assert refused.json()["error"] == OVER_CEILING
    assert app.knowledge_base.list_sources() == []


def test_the_ceiling_never_refuses_a_document_the_core_would_accept() -> None:
    """The cap is on the document and the ceiling is on the request carrying it, so the
    ceiling has to clear the cap by more than multipart costs — otherwise a file cora
    accepts is refused before it is read. What multipart costs is measured rather than
    assumed."""
    framing = int(
        httpx.Request(
            "POST",
            "http://cora/api/documents",
            files={"file": ("notes.md", NOTES, "text/markdown")},
        ).headers["content-length"]
    ) - len(NOTES)

    assert DEFAULT_MAX_BYTES + framing <= MAX_REQUEST_BYTES


def test_an_upload_that_does_not_say_how_large_it_is_is_refused() -> None:
    """A body of undeclared length cannot be bounded before it is read, and a ceiling
    any client can step around by chunking its upload is not a ceiling."""
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


def test_a_body_that_is_not_the_multipart_it_claims_says_so_as_a_sentence() -> None:
    """`MultipartParseError` is the parser's own, not a `CoreError`, so it walked past
    the handler and left `Internal Server Error` in a plain-text 500. The page reads a
    body it cannot parse as cora being unreachable — the one thing that is false when
    cora answered."""
    app = assembled()

    refused = client(app).post(
        "/api/documents",
        content=b"not multipart at all",
        headers={"content-type": "multipart/form-data; boundary=b0"},
    )

    assert refused.status_code == 400
    assert refused.headers["content-type"].startswith("application/json")
    assert refused.json()["error"] == UNREADABLE_UPLOAD
    assert app.knowledge_base.list_sources() == []


def test_a_form_part_starlette_itself_refuses_still_reads_as_json() -> None:
    """Not every refusal on this route is cora's: a field past the parser's own part
    size is Starlette's `HTTPException`, which answers in plain text. Whatever the
    sentence, the page has to be able to read it."""
    oversized = "y" * (1024 * 1024 + 10)
    body = (
        "--b0\r\n"
        'Content-Disposition: form-data; name="note"\r\n\r\n'
        f"{oversized}\r\n--b0--\r\n"
    ).encode()

    refused = client(assembled()).post(
        "/api/documents",
        content=body,
        headers={"content-type": "multipart/form-data; boundary=b0"},
    )

    assert refused.status_code == 400
    assert refused.headers["content-type"].startswith("application/json")
    assert refused.json()["error"]


UPLOAD_SCOPE = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": "1.1",
    "method": "POST",
    "path": "/api/documents",
    "raw_path": b"/api/documents",
    "root_path": "",
    "scheme": "http",
    "query_string": b"",
    "client": ("test", 1),
    "server": ("test", 80),
}


def test_nothing_is_read_from_a_request_over_the_ceiling() -> None:
    """The guard exists for the reading it prevents, and a status code cannot say
    whether anything was read: a body the parser chokes on answers 400 either way. So
    the app is driven directly, with a `receive` that fails the test if it is called."""
    served = api(assembled())
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        raise AssertionError("the body was read before the ceiling was applied")

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    scope = UPLOAD_SCOPE | {
        "headers": [
            (b"content-type", b"multipart/form-data; boundary=b0"),
            (b"content-length", str(MAX_REQUEST_BYTES + 1).encode()),
        ]
    }
    anyio.run(served, scope, receive, send)

    [start] = [each for each in sent if each["type"] == "http.response.start"]
    assert start["status"] == 413


def test_a_method_a_route_does_not_take_says_which_ones_it_does() -> None:
    """Starlette raises the 405 with the `Allow` header RFC 9110 requires on it, and a
    handler that answers in cora's own shape has to carry what it was raised with — a
    refusal the client cannot act on is worse than the plain text it replaced."""
    refused = client(assembled()).put("/api/documents")

    assert refused.status_code == 405
    # Both, though it is two routes that share the path — one of them raised this.
    assert {"GET", "POST"} <= set(refused.headers["allow"].split(", "))
    assert refused.json()["error"]


def _raising(error: Exception) -> Route:
    async def thrown(request: Request) -> Response:
        raise error

    return Route("/thrown", thrown, methods=["POST"])


def _refused_by(error: Exception) -> httpx.Response:
    """The app's own refusals, over a route that raises. The handlers are what is under
    test, and no real route can be made to fail in these ways on demand."""
    served = Starlette(routes=[_raising(error)], exception_handlers=REFUSALS)
    return TestClient(served).post("/thrown")


@pytest.mark.parametrize(
    "failure",
    [
        MultipartParseError("expected a boundary"),
        DecodeError("undecodable part"),
        QuerystringParseError("malformed querystring"),
    ],
    ids=lambda error: type(error).__name__,
)
def test_however_the_form_parser_fails_the_page_reads_a_sentence(
    failure: Exception,
) -> None:
    """`MultipartParseError` is one leaf of the parser's tree. Its siblings leave
    `Request.form()` the same way, and were still arriving as a plain-text 500 that the
    page reads as cora being unreachable."""
    refused = _refused_by(failure)

    assert refused.status_code == 400
    assert refused.json()["error"] == UNREADABLE_UPLOAD


@pytest.mark.parametrize("status", [204, 304])
def test_a_refusal_at_a_status_that_forbids_a_body_is_given_none(status: int) -> None:
    """The handler this one replaced omitted the body for these two, because a 204 or a
    304 carrying one is a response some clients will not read past."""
    answered = _refused_by(HTTPException(status_code=status))

    assert answered.status_code == status
    assert answered.content == b""


FITNESS, TRAVEL = "fitness", "travel"
KYOTO = b"The sleeper to Kyoto sells out a month before the maples turn."


def _scoped(app: App) -> TestClient:
    return TestClient(api(app, scopes=(FITNESS, TRAVEL)))


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


def test_an_upload_naming_no_field_lands_in_the_default_one() -> None:
    app = assembled()

    _scoped(app).post("/api/documents", files={"file": ("notes.md", NOTES, "text/md")})

    assert app.knowledge_base.list_sources(DEFAULT_SCOPE) == ["notes.md"]


def test_an_upload_naming_a_field_nobody_loaded_is_refused() -> None:
    app = assembled()

    refused = _scoped(app).post(
        "/api/documents",
        files={"file": ("kyoto.md", KYOTO, "text/markdown")},
        data={"scope": "../elsewhere"},
    )

    assert refused.status_code == 400
    assert TRAVEL in refused.json()["error"]
    assert app.knowledge_base.list_sources(DEFAULT_SCOPE) == []


def test_the_documents_listed_are_the_field_that_was_asked_for() -> None:
    app = assembled()
    client = _scoped(app)
    client.post(
        "/api/documents",
        files={"file": ("kyoto.md", KYOTO, "text/markdown")},
        data={"scope": TRAVEL},
    )
    client.post(
        "/api/documents",
        files={"file": ("notes.md", NOTES, "text/markdown")},
        data={"scope": FITNESS},
    )

    assert client.get(f"/api/documents?scope={TRAVEL}").json() == ["kyoto.md"]
    assert client.get(f"/api/documents?scope={FITNESS}").json() == ["notes.md"]


def test_a_passage_opens_from_its_own_field_and_no_other() -> None:
    app = assembled()
    client = _scoped(app)
    client.post(
        "/api/documents",
        files={"file": ("kyoto.md", KYOTO, "text/markdown")},
        data={"scope": TRAVEL},
    )
    upload = hashlib.sha256(KYOTO).hexdigest()

    assert (
        client.get(f"/api/uploads/{TRAVEL}/{upload}").json()["text"] == KYOTO.decode()
    )
    assert client.get(f"/api/uploads/{FITNESS}/{upload}").status_code == 404


def test_the_listing_refuses_a_field_nobody_loaded() -> None:
    """The name is the client's, and it reaches a collection the store would create for
    it: a route that took any name would grow the store on every request."""
    app = assembled()

    refused = _scoped(app).get("/api/documents?scope=invented")

    assert refused.status_code == 400
    assert TRAVEL in refused.json()["error"]


def test_a_passage_asked_for_under_a_field_nobody_loaded_is_not_an_outage() -> None:
    """A name no field has is the reader's mistake, not the store's: a 503 would tell
    them to retry something that cannot work, and `.hidden` reaching the store at all
    is a name the door should have stopped."""
    refused = _scoped(assembled()).get("/api/uploads/.hidden/abc123")

    assert refused.status_code == 400
    assert TRAVEL in refused.json()["error"]


def test_a_refusal_quotes_back_only_so_much_of_the_name_it_was_given() -> None:
    """The name is the client's, so what is echoed into a refusal is capped rather than
    reasoned about."""
    refused = _scoped(assembled()).get(f"/api/documents?scope={'z' * 5000}")

    assert refused.status_code == 400
    assert len(refused.json()["error"]) < 200
