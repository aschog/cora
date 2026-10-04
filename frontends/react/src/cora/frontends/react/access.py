import base64
import hmac

from starlette.datastructures import URL, Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class Access:
    def __init__(self, app: ASGIApp, *, token: str) -> None:
        self._app = app
        self._token = token.encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            if not self._authenticated(headers):
                response = JSONResponse(
                    {"error": "Authentication required."},
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="cora"'},
                )
                await response(scope, receive, send)
                return
            if scope["method"] not in {"GET", "HEAD", "OPTIONS"} and not _same_origin(
                scope, headers
            ):
                response = JSONResponse(
                    {"error": "Same-origin requests required."}, status_code=403
                )
                await response(scope, receive, send)
                return
        await self._app(scope, receive, send)

    def _authenticated(self, headers: Headers) -> bool:
        credentials = headers.getlist("authorization")
        if len(credentials) != 1:
            return False
        scheme, _, encoded = credentials[0].partition(" ")
        if scheme.lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except ValueError:
            return False
        username, separator, password = decoded.partition(b":")
        return (
            username == b"cora"
            and separator == b":"
            and hmac.compare_digest(password, self._token)
        )


def _same_origin(scope: Scope, headers: Headers) -> bool:
    origins = headers.getlist("origin")
    if not origins:
        return True
    return len(origins) == 1 and origins[0] == _origin(URL(scope=scope))


def _origin(url: URL) -> str:
    return f"{url.scheme}://{url.netloc}"
