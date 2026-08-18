"""The page's side of cora: one HTTP surface over an assembled `App`.

Every route hands back what the use cases already return, rendered by `payloads`. What
this module adds is the two things HTTP asks for and a screen does not: a status code
for a failure, and a stream for an answer that takes a minute to arrive.
"""

import pathlib
from collections.abc import Callable
from typing import Any

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from cora.app.assembly import App
from cora.domain.errors import AdapterError, CoreError
from cora.frontends.react import payloads

UNAVAILABLE = 503
"""What a store that went away answers with: the request was well formed and the
infrastructure behind it was not there, which is a different thing from a file cora
cannot read."""
REFUSED = 400
NO_CONTENT = 204


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
    return Starlette(routes=routes, exception_handlers={CoreError: _refused})


async def _refused(request: Request, error: Exception) -> JSONResponse:
    """No failure reaches the page as a traceback: what it reads is the message the
    error was raised with, under the code that says whose problem it is."""
    assert isinstance(error, CoreError)
    status = UNAVAILABLE if isinstance(error, AdapterError) else REFUSED
    return JSONResponse({"error": error.user_message}, status_code=status)


def _documents(app: App) -> Callable[[Request], Any]:
    def listed(request: Request) -> JSONResponse:
        return JSONResponse(app.knowledge_base.list_sources())

    return listed


def _ingest(app: App) -> Callable[[Request], Any]:
    async def add(request: Request) -> JSONResponse:
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
    def one(request: Request) -> Response:
        if app.memory is None:
            return JSONResponse({"error": NO_MEMORY}, status_code=404)
        app.memory.forget(request.path_params["key"])
        return Response(status_code=NO_CONTENT)

    return one


def _clear(app: App) -> Callable[[Request], Any]:
    def everything(request: Request) -> Response:
        if app.memory is None:
            return JSONResponse({"error": NO_MEMORY}, status_code=404)
        app.memory.clear()
        return Response(status_code=NO_CONTENT)

    return everything


NO_MEMORY = "This deployment keeps nothing between sessions."


def _plugins(plugins: tuple[str, ...]) -> Callable[[Request], Any]:
    def named(request: Request) -> JSONResponse:
        return JSONResponse(list(plugins))

    return named
