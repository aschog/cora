"""The page's side of cora: one HTTP surface over an assembled `App`.

Every route hands back what the use cases already return, rendered by `payloads`. What
this module adds is the two things HTTP asks for and a screen does not: a status code
for a failure, and a stream for an answer that takes a minute to arrive.
"""

import asyncio
import contextlib
import json
import logging
import pathlib
import threading
from collections.abc import AsyncIterator, Callable
from typing import Any

from python_multipart.exceptions import FormParserError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Match, Mount, Route
from starlette.staticfiles import StaticFiles

from cora.app.assembly import App
from cora.domain.errors import AdapterError, CoreError
from cora.domain.trace import TraceStep
from cora.engine.ingestion import DEFAULT_MAX_BYTES
from cora.engine.validation import MAX_INPUT_CHARS
from cora.frontends.react import payloads
from cora.ports.chat_model import Piece, Written

log = logging.getLogger(__name__)

UNAVAILABLE = 503
"""What a store that went away answers with: the request was well formed and the
infrastructure behind it was not there, which is a different thing from a file cora
cannot read."""
REFUSED = 400
NO_CONTENT = 204
TOO_LARGE = 413
NO_LENGTH_GIVEN = 411

MULTIPART_FRAMING = 64 * 1024
"""What a multipart body costs on top of the file inside it: two boundaries, the part's
headers, a filename. Generous, because refusing a document cora would accept is the one
thing the ceiling below must never do."""
MAX_REQUEST_BYTES = DEFAULT_MAX_BYTES + MULTIPART_FRAMING
"""The largest upload cora will read. The cap on a *document* is `ingest`'s, and it is
applied to a part the parser has already spooled to disk and read whole — so the request
carrying it is bounded here instead, before any of it is read."""


def api(
    app: App,
    *,
    plugins: tuple[str, ...] = (),
    ui: pathlib.Path | None = None,
) -> Starlette:
    """`plugins` is what the deployment configured, which the assembled app does not
    carry: the badge names them, and nothing on the page can change them."""
    routes: list[Route | Mount] = [
        Route("/api/documents", _documents(app), methods=["GET"]),
        Route("/api/documents", _ingest(app), methods=["POST"]),
        Route("/api/ask", _ask(app), methods=["POST"]),
        Route("/api/uploads/{upload}", _upload(app), methods=["GET"]),
        Route("/api/sessions", _sessions(app), methods=["GET"]),
        Route("/api/sessions/{thread_id}", _turns(app), methods=["GET"]),
        Route("/api/memory", _memory(app), methods=["GET"]),
        Route("/api/memory", _clear(app), methods=["DELETE"]),
        Route("/api/memory/{key}", _forget(app), methods=["DELETE"]),
        Route("/api/plugins", _plugins(plugins), methods=["GET"]),
    ]
    if ui is not None and ui.is_dir():
        routes.append(Mount("/", StaticFiles(directory=ui, html=True)))
    return Starlette(routes=routes, exception_handlers=REFUSALS)


async def _refused(request: Request, error: Exception) -> JSONResponse:
    """No failure reaches the page as a traceback: what it reads is the message the
    error was raised with, under the code that says whose problem it is."""
    assert isinstance(error, CoreError)
    status = UNAVAILABLE if isinstance(error, AdapterError) else REFUSED
    return JSONResponse({"error": error.user_message}, status_code=status)


async def _unreadable(request: Request, error: Exception) -> JSONResponse:
    """A body the form parser could not read, however it could not read it. The parser's
    exceptions are its own rather than `CoreError`s, so they walked past `_refused` and
    left the page a plain-text 500 — which `api.ts` reads as cora being unreachable, the
    one thing that is false when cora answered. Registered on the family's base class:
    the leaf that was reported has siblings, and they leave `Request.form()` alike."""
    return JSONResponse({"error": UNREADABLE_UPLOAD}, status_code=REFUSED)


async def _as_sentence(request: Request, error: Exception) -> Response:
    """Starlette's own refusals — a path with no route, a method a route does not take,
    a form field past the parser's part size — answer in plain text. The page reads
    every failure as JSON, so they leave here as JSON too, under the code and the
    headers they were raised with: the `Allow` on a 405 is the only part of it the
    client can act on. A status that forbids a body is given none, whatever there was to
    say."""
    assert isinstance(error, HTTPException)
    headers = dict(error.headers or {}) | _allowed(request, error.status_code)
    if error.status_code in BODILESS:
        return Response(status_code=error.status_code, headers=headers)
    return JSONResponse(
        {"error": error.detail}, status_code=error.status_code, headers=headers
    )


def _allowed(request: Request, status: int) -> dict[str, str]:
    """Every method the app answers on this path. Starlette raises the 405 from the one
    route that did not match, which can only name its own methods — and two routes over
    one path is how a GET and a POST sharing a URL are written here, so that header
    tells the client the other one is not allowed."""
    if status != NOT_THAT_WAY:
        return {}
    served = {
        method
        for route in request.app.routes
        if isinstance(route, Route)
        and route.matches(request.scope)[0] is not Match.NONE
        for method in route.methods or ()
    }
    return {"Allow": ", ".join(sorted(served))} if served else {}


NOT_THAT_WAY = 405
BODILESS = frozenset({204, 304})
"""Statuses a response may not carry a body under. A client that reads one anyway is
reading the next response on the connection."""

REFUSALS: dict[Any, Any] = {
    CoreError: _refused,
    FormParserError: _unreadable,
    HTTPException: _as_sentence,
}
"""Every failure this app answers, and the shape it answers in. Named rather than built
inside `api` so a handler can be driven by a test over a route that fails on demand —
no real route can be made to fail these ways."""


def _documents(app: App) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        return JSONResponse(app.knowledge_base.list_sources())

    return listed


def _ingest(app: App) -> Callable[[Request], Any]:
    async def add(request: Request) -> JSONResponse:
        refused = _over_ceiling(request)
        if refused is not None:
            return refused
        async with request.form() as form:
            uploaded = form.get("file")
            if not isinstance(uploaded, UploadFile):
                return JSONResponse({"error": NO_FILE}, status_code=REFUSED)
            filename = uploaded.filename or ""
            data = await uploaded.read()
        chunks = await run_in_threadpool(app.knowledge_base.add_file, data, filename)
        return JSONResponse({"document": filename, "chunks": chunks})

    return add


NO_FILE = "No file was uploaded."
UNREADABLE_UPLOAD = "That upload did not arrive as a file cora could read."
MEGABYTE = 1024 * 1024
OVER_CEILING = (
    f"That upload is larger than the {DEFAULT_MAX_BYTES // MEGABYTE} MB cora reads."
)
NO_LENGTH = "An upload has to say how large it is."


def _over_ceiling(request: Request) -> JSONResponse | None:
    """What the request declares, settled before a byte of it is read: a length cora
    will not read past, and a body that declares none at all — a ceiling any client can
    step around by chunking its upload is not a ceiling."""
    declared = request.headers.get("content-length", "")
    if not declared.isdigit():
        return JSONResponse({"error": NO_LENGTH}, status_code=NO_LENGTH_GIVEN)
    if int(declared) > MAX_REQUEST_BYTES:
        return JSONResponse({"error": OVER_CEILING}, status_code=TOO_LARGE)
    return None


STREAM = "text/event-stream"
UNBUFFERED = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
"""A proxy that buffers the response undoes the endpoint: the steps would arrive
together at the end, which is the shape this exists not to have."""
NOT_A_QUESTION = "Ask with a question and the thread it belongs to."
ESCAPED_CHARACTER_BYTES = 12
"""The most one character of a question can cost on the wire. The page sends raw UTF-8,
where the widest character is four bytes; a client that escapes non-ASCII writes that
same character as two `\\uXXXX` sequences. A ceiling sized for the page alone refuses
questions cora would answer, and the difference is kilobytes."""
MAX_ASK_BYTES = MAX_INPUT_CHARS * ESCAPED_CHARACTER_BYTES + 1024
"""What a question may weigh, with a kilobyte over it for the thread id and the JSON
around the two. Whether the question is too long is the engine's rule — this is only how
much cora reads to find out."""
TOO_LONG_TO_ASK = "That question is longer than cora reads."
WENT_WRONG = "Something went wrong answering that. Please try again."
"""What an unmodelled failure says. A `CoreError` was written to be read by whoever
asked; anything else was not, so its text goes to the log and the reader gets a sentence
that is true without quoting a stack."""
DONE = None
"""What the worker puts on the queue when there is nothing further to send. A stream
that is not closed is a page still spinning under an answer that already failed."""


def _ask(app: App) -> Callable[[Request], Any]:
    """A turn takes as long as it takes, so it is a stream: the steps as the agent takes
    them, the answer in the pieces it is written in, then the answer whole, and either
    way an end. The whole one is what the page keeps — the pieces are it arriving early.

    A turn may take several rounds and only the last of them is the answer, so a model
    that writes before it calls a tool writes something that is not one. `aside` says
    that: the pieces before it were that writing, and a client drops them. So the pieces
    since the last `aside` are what the `turn` event carries, and no client has to infer
    a round boundary from the shape of the step stream.

    `Agent.answer` blocks and reports its steps from the thread it runs on, so the turn
    runs on a thread of its own and hands each event to the event loop. The loop waits
    on an `asyncio.Queue` rather than on a worker thread parked in `Queue.get`: a thread
    parked there holds one of the pool's slots for the whole turn — the same pool every
    other endpoint on this page is served from — and cannot be cancelled, so a reader
    who closes the tab keeps the slot until the model is done with a turn nobody is
    waiting for."""

    async def taken(request: Request) -> Response:
        body = await _read_within(request, MAX_ASK_BYTES)
        if body is None:
            return JSONResponse({"error": TOO_LONG_TO_ASK}, status_code=TOO_LARGE)
        try:
            asked = json.loads(body)
        except ValueError:
            return JSONResponse({"error": NOT_A_QUESTION}, status_code=REFUSED)
        if not isinstance(asked, dict):
            return JSONResponse({"error": NOT_A_QUESTION}, status_code=REFUSED)
        question, thread_id = asked.get("question"), asked.get("thread_id")
        if not _said(question) or not _said(thread_id):
            return JSONResponse({"error": NOT_A_QUESTION}, status_code=REFUSED)
        events: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def deliver(event: str | None) -> None:
            """The worker's only reach into the loop. A page closed mid-turn takes the
            loop with it in tests and at shutdown; the turn is then simply unheard."""
            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(events.put_nowait, event)

        turn = threading.Thread(
            target=_run,
            args=(app, question, thread_id, deliver),
            daemon=True,
        )

        async def body() -> AsyncIterator[str]:
            turn.start()
            while (event := await events.get()) is not DONE:
                yield event

        return StreamingResponse(body(), media_type=STREAM, headers=UNBUFFERED)

    return taken


async def _read_within(request: Request, ceiling: int) -> bytes | None:
    """The body, read with a stop on it. The upload route's trick — refusing on the
    length the request declares — is no use to a route that must also read a body which
    declares none, and `json()` buffers whatever arrives. So the bound is on the reading
    itself, and what comes back is `None` when there was more of it than that."""
    read = bytearray()
    async for chunk in request.stream():
        read.extend(chunk)
        if len(read) > ceiling:
            return None
    return bytes(read)


def _said(half: Any) -> bool:
    """What the endpoint's own refusal promises: a question, and the thread it belongs
    to. Blank is neither — a turn asked with no question costs a worker thread and a
    graph run, and one asked with no thread is recorded where nobody can reopen it."""
    return isinstance(half, str) and bool(half.strip())


def _run(
    app: App,
    question: str,
    thread_id: str,
    deliver: Callable[[str | None], None],
) -> None:
    def report(step: TraceStep) -> None:
        deliver(_event("step", payloads.step(step)))

    def write(written: Written) -> None:
        if isinstance(written, Piece):
            deliver(_event("text", {"text": written.text}))
        else:
            deliver(_event("aside", {}))

    try:
        result = app.agent.answer(question, thread_id, report, write)
        deliver(_event("turn", payloads.result(result)))
    except CoreError as refused:
        deliver(_event("error", {"error": refused.user_message}))
    except Exception:
        log.exception("the turn failed in a way nobody modelled")
        deliver(_event("error", {"error": WENT_WRONG}))
    finally:
        deliver(DONE)


def _event(name: str, data: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


def _upload(app: App) -> Callable[[Request], Any]:
    def read(request: Request) -> JSONResponse:
        text = app.knowledge_base.text(request.path_params["upload"])
        if text is None:
            return JSONResponse({"error": UNKEPT}, status_code=404)
        return JSONResponse({"text": text})

    return read


UNKEPT = "That passage's document was never kept, so it cannot be opened."


def _sessions(app: App) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        if app.conversations is None:
            return JSONResponse([])
        return JSONResponse(
            [payloads.session(each) for each in app.conversations.sessions()]
        )

    return listed


def _turns(app: App) -> Callable[[Request], Any]:
    def kept(request: Request) -> JSONResponse:
        if app.conversations is None:
            return JSONResponse([])
        turns = app.conversations.turns(request.path_params["thread_id"])
        return JSONResponse([payloads.turn(each) for each in turns])

    return kept


def _memory(app: App) -> Callable[[Request], Any]:
    def recalled(request: Request) -> JSONResponse:
        if app.memory is None:
            return JSONResponse([])
        return JSONResponse([payloads.fact(each) for each in app.memory.recall()])

    return recalled


def _forget(app: App) -> Callable[[Request], Any]:
    """A deployment with no memory slot has nothing to forget, so forgetting is
    already done — the same reading as the panels, where no store is empty rather
    than broken."""

    def one(request: Request) -> Response:
        if app.memory is not None:
            app.memory.forget(request.path_params["key"])
        return Response(status_code=NO_CONTENT)

    return one


def _clear(app: App) -> Callable[[Request], Any]:
    def everything(request: Request) -> Response:
        if app.memory is not None:
            app.memory.clear()
        return Response(status_code=NO_CONTENT)

    return everything


def _plugins(plugins: tuple[str, ...]) -> Callable[[Request], Any]:
    def named(request: Request) -> JSONResponse:
        return JSONResponse(list(plugins))

    return named
