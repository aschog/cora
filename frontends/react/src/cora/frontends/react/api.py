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

from cora.app.assembly import App, LiveApp
from cora.domain.card import Answer
from cora.domain.chat_result import ChatResult
from cora.domain.decision import TurnPaused
from cora.domain.errors import AdapterError, CoreError, NothingToResumeError
from cora.domain.trace import TraceStep
from cora.engine.ingestion import DEFAULT_MAX_BYTES
from cora.engine.removal import deletable, fields_going
from cora.engine.validation import MAX_INPUT_CHARS
from cora.frontends.react import payloads
from cora.ports.chat_model import Piece, TextSink, Written
from cora.ports.host import DEFAULT_SCOPE

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


Apps = Callable[[], App]
"""How a handler reads the app: taken once per request, so a turn runs whole on the
composition it started with, whatever the plugins folder does meanwhile."""


def api(
    app: App | LiveApp,
    *,
    ui: pathlib.Path | None = None,
) -> Starlette:
    """One HTTP surface over the app, reading everything off the composition itself —
    the fields it offers included, because a live plugins folder makes those a fact of
    the composition rather than a setting. What loaded is the app's own listing, so
    the menu and a terminal say one thing.

    Handed a `LiveApp`, every request reads the composition the plugins folder
    describes by then; handed an `App`, the page serves that one for good."""
    apps = app.current if isinstance(app, LiveApp) else (lambda: app)
    routes: list[Route | Mount] = [
        Route("/api/documents", _documents(apps), methods=["GET"]),
        Route("/api/documents", _ingest(apps), methods=["POST"]),
        Route(
            "/api/documents/{scope}/{name}",
            _delete_document(apps),
            methods=["DELETE"],
        ),
        Route("/api/ask", _ask(apps), methods=["POST"]),
        Route("/api/resume", _resume(apps), methods=["POST"]),
        Route("/api/uploads/{scope}/{upload}", _upload(apps), methods=["GET"]),
        Route("/api/sessions", _sessions(apps), methods=["GET"]),
        Route("/api/sessions/{thread_id}", _turns(apps), methods=["GET"]),
        Route("/api/sessions/{thread_id}", _delete(apps), methods=["DELETE"]),
        Route("/api/sessions/{thread_id}/pending", _pending(apps), methods=["GET"]),
        Route("/api/sessions/{thread_id}/scope", _scope(apps), methods=["GET"]),
        Route("/api/memory", _memory(apps), methods=["GET"]),
        Route("/api/memory", _clear(apps), methods=["DELETE"]),
        Route("/api/memory/{key}", _forget(apps), methods=["DELETE"]),
        Route("/api/plugins", _plugins(apps), methods=["GET"]),
        Route("/api/plugins/{name}", _delete_plugin(apps), methods=["DELETE"]),
        Route("/api/scopes", _scopes(apps), methods=["GET"]),
    ]
    if ui is not None and ui.is_dir():
        routes.append(Mount("/", StaticFiles(directory=ui, html=True)))
    return Starlette(routes=routes, exception_handlers=REFUSALS)


async def _refused(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, CoreError)
    status = UNAVAILABLE if isinstance(error, AdapterError) else REFUSED
    return JSONResponse({"error": error.user_message}, status_code=status)


async def _unreadable(request: Request, error: Exception) -> JSONResponse:
    return JSONResponse({"error": UNREADABLE_UPLOAD}, status_code=REFUSED)


async def _as_sentence(request: Request, error: Exception) -> Response:
    assert isinstance(error, HTTPException)
    headers = dict(error.headers or {}) | _allowed(request, error.status_code)
    if error.status_code in BODILESS:
        return Response(status_code=error.status_code, headers=headers)
    return JSONResponse(
        {"error": error.detail}, status_code=error.status_code, headers=headers
    )


def _allowed(request: Request, status: int) -> dict[str, str]:
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


def _documents(apps: Apps) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        app = apps()
        named = request.query_params.get("scope", "")
        scope = _field(named, app.scopes)
        if scope is None:
            return _refusal(named, app.scopes)
        return JSONResponse(app.knowledge_base.list_sources(scope))

    return listed


def _delete_document(apps: Apps) -> Callable[[Request], Any]:
    def one(request: Request) -> Response:
        app = apps()
        named = request.path_params["scope"]
        scope = _field(named, app.scopes)
        if scope is None:
            return _refusal(named, app.scopes)
        app.knowledge_base.forget(scope, request.path_params["name"])
        return Response(status_code=NO_CONTENT)

    return one


def _refusal(named: str, scopes: tuple[str, ...]) -> JSONResponse:
    return JSONResponse({"error": _no_such_field(named, scopes)}, status_code=REFUSED)


def _field(named: str, scopes: tuple[str, ...]) -> str | None:
    asked = named or DEFAULT_SCOPE
    return asked if asked in (*scopes, DEFAULT_SCOPE) else None


def _ingest(apps: Apps) -> Callable[[Request], Any]:
    async def add(request: Request) -> JSONResponse:
        # Off the loop: reading the current app may recompose over a changed plugins
        # folder, and that work — imports included — must not hold every other request.
        app = await run_in_threadpool(apps)
        refused = _over_ceiling(request)
        if refused is not None:
            return refused
        async with request.form() as form:
            uploaded = form.get("file")
            if not isinstance(uploaded, UploadFile):
                return JSONResponse({"error": NO_FILE}, status_code=REFUSED)
            named = str(form.get("scope") or "")
            filename = uploaded.filename or ""
            data = await uploaded.read()
        scope = _field(named, app.scopes)
        if scope is None:
            return _refusal(named, app.scopes)
        chunks = await run_in_threadpool(
            app.knowledge_base.add_file, data, filename, scope
        )
        return JSONResponse({"document": filename, "chunks": chunks, "scope": scope})

    return add


MOST_OF_A_NAME = 40
"""How much of a name a refusal quotes back. The name is the client's, so what is echoed
is capped rather than reasoned about."""


def _no_such_field(named: str, scopes: tuple[str, ...]) -> str:
    offered = ", ".join((*scopes, DEFAULT_SCOPE))
    asked = named[:MOST_OF_A_NAME]
    return f"There is no field called {asked!r}. This cora has: {offered}."


NO_FILE = "No file was uploaded."
UNREADABLE_UPLOAD = "That upload did not arrive as a file cora could read."
MEGABYTE = 1024 * 1024
OVER_CEILING = (
    f"That upload is larger than the {DEFAULT_MAX_BYTES // MEGABYTE} MB cora reads."
)
NO_LENGTH = "An upload has to say how large it is."


def _over_ceiling(request: Request) -> JSONResponse | None:
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
NOT_A_DECISION = (
    "Settling a card needs the conversation it belongs to, and the action taken."
)
"""What a malformed answer is refused with. Both, because an answer bound to nothing is
not one: a missing action would settle whichever card happened to be outstanding, and
must not read as a decline either."""
NOT_FILLED_IN = "The values written into a card have to be a JSON object."
NOT_THAT_CARD = (
    "That is not one of the ways off the card this conversation is waiting on."
)
"""What an answer naming an action nobody offered is refused with. The step waiting
would read it as a decline, which is safe and says nothing — so a page holding a card
the conversation has moved past is told, rather than settling the turn on its behalf."""
NO_SUCH_SCOPE = (
    "cora is not running that field, so a conversation cannot be pinned to it."
)
WENT_WRONG = "Something went wrong answering that. Please try again."
"""What an unmodelled failure says. A `CoreError` was written to be read by whoever
asked; anything else was not, so its text goes to the log and the reader gets a sentence
that is true without quoting a stack."""
DONE = None
"""What the worker puts on the queue when there is nothing further to send. A stream
that is not closed is a page still spinning under an answer that already failed."""


def _ask(apps: Apps) -> Callable[[Request], Any]:
    async def taken(request: Request) -> Response:
        app = await run_in_threadpool(apps)
        asked = await _json_object(request, NOT_A_QUESTION)
        if isinstance(asked, JSONResponse):
            return asked
        question, thread_id = asked.get("question"), asked.get("thread_id")
        if not _said(question) or not _said(thread_id):
            return JSONResponse({"error": NOT_A_QUESTION}, status_code=REFUSED)
        pinned = asked.get("pin")
        # A field nobody loaded would pin the thread to a scope no registration is
        # under, and a pin cannot be undone — so it is refused here, where what the
        # deployment offers is known, rather than fixed forever inside the turn.
        if pinned is not None and pinned not in app.scopes:
            return JSONResponse({"error": NO_SUCH_SCOPE}, status_code=REFUSED)
        return _streaming(
            lambda report, write: app.agent.answer(
                question, thread_id, report, write, pin=pinned
            )
        )

    return taken


def _resume(apps: Apps) -> Callable[[Request], Any]:
    async def picked(request: Request) -> Response:
        app = await run_in_threadpool(apps)
        answered = await _json_object(request, NOT_A_DECISION)
        if isinstance(answered, JSONResponse):
            return answered
        thread_id, action = answered.get("thread_id"), answered.get("answer")
        # `answer` must be *said*, even to say nothing: a body that leaves it out reads
        # the same as one that declines, so a client with a typo in the field silently
        # tells the model the reader rejected every option.
        if "answer" not in answered:
            return JSONResponse({"error": NOT_A_DECISION}, status_code=REFUSED)
        if not _said(thread_id) or not (action is None or _said(action)):
            return JSONResponse({"error": NOT_A_DECISION}, status_code=REFUSED)
        values = answered.get("values", {})
        if not isinstance(values, dict):
            return JSONResponse({"error": NOT_FILLED_IN}, status_code=REFUSED)
        waiting = await run_in_threadpool(app.agent.pending, thread_id)
        if waiting is None:
            raise NothingToResumeError
        # Not merely "something is pending": an action nobody offered would be read by
        # the step waiting as a decline — safe, and silent. A page whose card has moved
        # on is refused where whoever sent it can still see it, rather than quietly
        # settling the reader's turn the other way.
        if action is not None and action not in {
            offered.answer for offered in waiting.card.actions
        }:
            return JSONResponse({"error": NOT_THAT_CARD}, status_code=REFUSED)
        # A card names the fields it asks for and marks which of them are the reader's;
        # a value for anything else reached the run from outside it and is dropped, so a
        # request cannot write an argument the card put up to be read.
        writable = {field.name for field in waiting.card.fields if field.editable}
        settled = Answer(
            action=action,
            values={name: v for name, v in values.items() if name in writable},
        )
        return _streaming(
            lambda report, write: app.agent.resume(settled, thread_id, report, write)
        )

    return picked


def _pending(apps: Apps) -> Callable[[Request], Any]:
    def waiting(request: Request) -> JSONResponse:
        parked = apps().agent.pending(request.path_params["thread_id"])
        return JSONResponse(None if parked is None else payloads.pending(parked))

    return waiting


def _streaming(turning: "Turning") -> StreamingResponse:
    events: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def deliver(event: str | None) -> None:
        """The worker's only reach into the loop. A page closed mid-turn takes the
        loop with it in tests and at shutdown; the turn is then simply unheard."""
        with contextlib.suppress(RuntimeError):
            loop.call_soon_threadsafe(events.put_nowait, event)

    turn = threading.Thread(target=_run, args=(turning, deliver), daemon=True)

    async def body() -> AsyncIterator[str]:
        turn.start()
        while (event := await events.get()) is not DONE:
            yield event

    return StreamingResponse(body(), media_type=STREAM, headers=UNBUFFERED)


async def _read_within(request: Request, ceiling: int) -> bytes | None:
    read = bytearray()
    async for chunk in request.stream():
        read.extend(chunk)
        if len(read) > ceiling:
            return None
    return bytes(read)


async def _json_object(request: Request, refusal: str) -> Any:
    body = await _read_within(request, MAX_ASK_BYTES)
    if body is None:
        return JSONResponse({"error": TOO_LONG_TO_ASK}, status_code=TOO_LARGE)
    try:
        parsed = json.loads(body)
    except ValueError:
        return JSONResponse({"error": refusal}, status_code=REFUSED)
    if not isinstance(parsed, dict):
        return JSONResponse({"error": refusal}, status_code=REFUSED)
    return parsed


def _said(half: Any) -> bool:
    return isinstance(half, str) and bool(half.strip())


Turning = Callable[[Callable[[TraceStep], None], TextSink], ChatResult]
"""A turn waiting to be walked: begun, or picked up from where it stopped. Both report
their steps and write their text the same way, so the stream above is told how to run
one rather than which of the two it is."""


def _run(turning: Turning, deliver: Callable[[str | None], None]) -> None:
    def report(step: TraceStep) -> None:
        deliver(_event("step", payloads.step(step)))

    def write(written: Written) -> None:
        if isinstance(written, Piece):
            deliver(_event("text", {"text": written.text}))
        else:
            deliver(_event("aside", {}))

    try:
        result = turning(report, write)
        deliver(_event("turn", payloads.result(result)))
    except TurnPaused as waiting:
        deliver(_event("paused", payloads.pending(waiting.pending)))
    except CoreError as refused:
        deliver(_event("error", {"error": refused.user_message}))
    except Exception:
        log.exception("the turn failed in a way nobody modelled")
        deliver(_event("error", {"error": WENT_WRONG}))
    finally:
        deliver(DONE)


def _event(name: str, data: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(data)}\n\n"


def _upload(apps: Apps) -> Callable[[Request], Any]:
    def read(request: Request) -> JSONResponse:
        app = apps()
        named = request.path_params["scope"]
        scope = _field(named, app.scopes)
        if scope is None:
            return _refusal(named, app.scopes)
        text = app.knowledge_base.text(scope, request.path_params["upload"])
        if text is None:
            return JSONResponse({"error": UNKEPT}, status_code=404)
        return JSONResponse({"text": text})

    return read


UNKEPT = "cora cannot open that passage's document."
"""One sentence for either way a document is not there. The store cannot tell a
deleted document from one whose text was never kept — both read as nothing — so what
the reader is told is true of both rather than guessing between them."""


def _sessions(apps: Apps) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        app = apps()
        if app.conversations is None:
            return JSONResponse([])
        return JSONResponse(
            [payloads.session(each) for each in app.conversations.sessions()]
        )

    return listed


def _turns(apps: Apps) -> Callable[[Request], Any]:
    def kept(request: Request) -> JSONResponse:
        app = apps()
        if app.conversations is None:
            return JSONResponse([])
        turns = app.conversations.turns(request.path_params["thread_id"])
        return JSONResponse([payloads.turn(each) for each in turns])

    return kept


def _delete(apps: Apps) -> Callable[[Request], Any]:
    def one(request: Request) -> Response:
        apps().agent.forget(request.path_params["thread_id"])
        return Response(status_code=NO_CONTENT)

    return one


def _memory(apps: Apps) -> Callable[[Request], Any]:
    def recalled(request: Request) -> JSONResponse:
        app = apps()
        if app.memory is None:
            return JSONResponse([])
        return JSONResponse([payloads.fact(each) for each in app.memory.recall()])

    return recalled


def _forget(apps: Apps) -> Callable[[Request], Any]:
    def one(request: Request) -> Response:
        app = apps()
        if app.memory is not None:
            app.memory.forget(request.path_params["key"])
        return Response(status_code=NO_CONTENT)

    return one


def _clear(apps: Apps) -> Callable[[Request], Any]:
    def everything(request: Request) -> Response:
        app = apps()
        if app.memory is not None:
            app.memory.clear()
        return Response(status_code=NO_CONTENT)

    return everything


def _plugins(apps: Apps) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        app = apps()
        return JSONResponse(
            [
                payloads.plugin(
                    each,
                    deletable(each, app.plugins_folder),
                    fields_going(each, app.plugins, app.configured),
                )
                for each in app.plugins
            ]
        )

    return listed


def _delete_plugin(apps: Apps) -> Callable[[Request], Any]:
    def one(request: Request) -> Response:
        apps().remove(request.path_params["name"])
        return Response(status_code=NO_CONTENT)

    return one


def _scopes(apps: Apps) -> Callable[[Request], Any]:
    def offered(request: Request) -> JSONResponse:
        return JSONResponse(
            {"available": list(apps().scopes), "default": DEFAULT_SCOPE}
        )

    return offered


def _scope(apps: Apps) -> Callable[[Request], Any]:
    def held(request: Request) -> JSONResponse:
        pin = apps().agent.pinned(request.path_params["thread_id"])
        return JSONResponse({"pin": pin})

    return held
