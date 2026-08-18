import hashlib
import pathlib
from collections.abc import Iterator

import httpx
import pytest
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
    api,
)
from fakes import FailingConversations, FailingMemory, FakeConversations, FakeMemory

NOTES = b"Squats stall on sleep, not on volume. The block holds intensity."


def client(
    app: App,
    *,
    plugins: tuple[str, ...] = (),
    ui: pathlib.Path | None = None,
) -> TestClient:
    return TestClient(api(app, plugins=plugins, ui=ui))


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
    assert added.json() == {"document": "notes.md", "chunks": 1}
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

    kept = client(app).get(f"/api/uploads/{upload}")

    assert kept.status_code == 200
    assert kept.json()["text"] == NOTES.decode()


def test_an_upload_never_kept_says_so_rather_than_serving_an_empty_document() -> None:
    missing = client(assembled()).get("/api/uploads/nothingwaskeptunderthis")

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


def test_the_plugins_endpoint_names_what_the_deployment_configured() -> None:
    named = client(assembled(), plugins=("cora.plugins.fitness",)).get("/api/plugins")

    assert named.json() == ["cora.plugins.fitness"]


def test_with_no_plugin_configured_the_page_is_told_bare_cora() -> None:
    assert client(assembled()).get("/api/plugins").json() == []


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
