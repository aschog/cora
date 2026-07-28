import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast


class StubLlm:
    """Stands in for OpenRouter at the *network* seam rather than the object
    seam: during an e2e run the openai client lives in the Streamlit
    subprocess, where in-process doubles cannot reach it. Threading, because
    Streamlit reruns can overlap."""

    def __init__(self) -> None:
        self._answer = ""
        self._tool_call: tuple[str, dict[str, Any]] | None = None
        self._endless = False
        self._status = 200
        self._requests: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._overlap: threading.Barrier | None = None
        self._delay = 0.0
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
        if self._thread.is_alive():
            raise RuntimeError("the stub server thread did not stop")

    @property
    def base_url(self) -> str:
        host, port = cast(tuple[str, int], self._server.server_address)
        return f"http://{host}:{port}/v1"

    @property
    def requests(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._requests)

    def script_answer(self, text: str) -> None:
        self._answer = text

    def script_tool_call(self, name: str, arguments: dict[str, Any]) -> None:
        self._tool_call = (name, arguments)

    def script_endless_tool_calls(self, name: str, arguments: dict[str, Any]) -> None:
        self._tool_call = (name, arguments)
        self._endless = True

    def script_status(self, code: int) -> None:
        self._status = code

    def require_overlap(self, count: int) -> None:
        self._overlap = threading.Barrier(count, timeout=10)

    def script_delay(self, seconds: float) -> None:
        self._delay = seconds

    def response(self, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        with self._lock:
            self._requests.append(request)
        overlap = self._overlap
        if overlap is not None:
            overlap.wait()
            self._overlap = None  # after the trip: clearing first strands the waiter
        if self._delay:
            time.sleep(self._delay)
        if self._status != 200:
            return self._status, {
                "error": {"message": "scripted failure", "code": self._status}
            }
        if self._tool_call is not None and (
            self._endless or not _carries_tool_result(request)
        ):
            return 200, _envelope("tool_calls", _tool_call_message(*self._tool_call))
        return 200, _envelope("stop", {"role": "assistant", "content": self._answer})


def _carries_tool_result(request: dict[str, Any]) -> bool:
    return any(
        message.get("role") == "tool" for message in request.get("messages") or []
    )


def _tool_call_message(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
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


def _envelope(finish_reason: str, message: dict[str, Any]) -> dict[str, Any]:
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
