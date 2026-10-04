from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class Access:
    def __init__(self, app: ASGIApp, *, token: str) -> None:
        self._app = app
        self._token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not Headers(scope=scope).get("authorization"):
            response = JSONResponse(
                {"error": "Authentication required."},
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="cora"'},
            )
            await response(scope, receive, send)
            return
        await self._app(scope, receive, send)
