import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast


class StubLlm:
    """Stands in for OpenRouter at the *network* seam rather than the object
    seam: during an e2e run the openai client lives in the Streamlit
    subprocess, where in-process doubles cannot reach it. Threading, because
    Streamlit reruns can overlap."""

    def __init__(self) -> None:
        self._answer = ""
        self._tool_call: tuple[str, dict[str, object]] | None = None
        self._status = 200
        self._server = _StubServer(("127.0.0.1", 0), _Handler)
        self._server.stub = self
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> "StubLlm":
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    @property
    def base_url(self) -> str:
        host, port = cast(tuple[str, int], self._server.server_address)
        return f"http://{host}:{port}/v1"

    def script_answer(self, text: str) -> None:
        self._answer = text

    def script_tool_call(self, name: str, arguments: dict[str, object]) -> None:
        self._tool_call = (name, arguments)

    def script_status(self, code: int) -> None:
        """A scripted failure stands until cleared: the client retries 429 and 5xx
        three times by default, and every attempt must see the same failure."""
        self._status = code

    def response(self, request: dict[str, object]) -> tuple[int, dict[str, object]]:
        """Keyed on conversation state, never on a call counter: the openai
        client retries by default, so identical requests repeat."""
        if self._status != 200:
            return self._status, {
                "error": {"message": "scripted failure", "code": self._status}
            }
        if self._tool_call is not None and not _carries_tool_result(request):
            return 200, _envelope("tool_calls", _tool_call_message(*self._tool_call))
        return 200, _envelope("stop", {"role": "assistant", "content": self._answer})


def _carries_tool_result(request: dict[str, object]) -> bool:
    messages = cast(list[dict[str, object]], request.get("messages") or [])
    return any(message.get("role") == "tool" for message in messages)


def _tool_call_message(name: str, arguments: dict[str, object]) -> dict[str, object]:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": f"call_{name}",
                "type": "function",
                # A JSON string, not an object: an object fails client validation.
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
        ],
    }


def _envelope(finish_reason: str, message: dict[str, object]) -> dict[str, object]:
    return {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "created": 0,
        "model": "stub-model",
        "choices": [{"index": 0, "finish_reason": finish_reason, "message": message}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


class _StubServer(ThreadingHTTPServer):
    stub: StubLlm


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        stub = cast(_StubServer, self.server).stub
        status, payload = stub.response(json.loads(raw or b"{}"))
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Drop the per-request stderr line; pytest output stays readable."""
