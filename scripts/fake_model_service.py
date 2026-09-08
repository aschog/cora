"""An OpenAI-compatible model, for driving cora end to end with no key and no network.

`OPENROUTER_BASE_URL` is a setting like any other, and `langchain-openai` is what talks
to it — so a local server that answers `/chat/completions` in the provider's own shape
puts the whole of cora under test: the real page, the real API, the real stores, the
real turn. What it cannot test is the provider, which is what `make e2e-live` is for.

It replies to a keyword in the question rather than reading it, so a run is the same
every time. What the browser suite types is what steers it:

    search …   call the document search, then answer citing the passage
    choose …   stop the turn and ask which of two values was meant
    remember … keep a fact about the user
    write …    call a tool that changes something outside cora, so the gate stops it
    anything   answer in prose, streamed a word at a time

A tool it was not offered is never called: the reply falls back to prose, so a
deployment loading none of them still answers.

    uv run python scripts/fake_model_service.py        # 127.0.0.1:8911
"""

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "127.0.0.1"
PORT = 8911
CITED = "The note says protein builds muscle [1]."
PROSE = "Hello. Ask me about your documents and I will search them."
KEPT = "Noted."
WROTE = "Done — it is written."
READY = b"the fake model is up\n"

# What a keyword asks for: the tool to call and the arguments to call it with. Read in
# order, so the first keyword in the question wins.
CALLS: tuple[tuple[str, str, dict[str, Any]], ...] = (
    ("search", "search_documents", {"query": "protein"}),
    (
        "choose",
        "ask_user",
        {
            "question": "Which weight did you mean?",
            "options": [
                {"label": "75 kg", "note": "February"},
                {"label": "77 kg", "note": "last week"},
            ],
            "decline": "Neither, thanks.",
        },
    ),
    ("remember", "remember", {"fact": "The user trains on Tuesdays."}),
    ("write", "write_note", {"title": "note", "body": "what the turn worked out"}),
)


def reply_to(body: dict[str, Any]) -> tuple[str | None, str, dict[str, Any]]:
    """What to answer with: prose, or a call to one of the tools on offer."""
    messages = body.get("messages", [])
    offered = {
        tool.get("function", {}).get("name") for tool in body.get("tools", []) or []
    }
    if messages and messages[-1].get("role") == "tool":
        # A passage reaches the model numbered, so the number is what says there is
        # something to cite — the answer carries it back, or the citation is nobody's.
        answered = str(messages[-1].get("content", ""))
        if "[1]" in answered:
            return None, CITED, {}
        return None, WROTE if answered.startswith("written to") else KEPT, {}
    asked = last_question(messages)
    for keyword, tool, arguments in CALLS:
        if re.search(rf"\b{keyword}\b", asked) and tool in offered:
            return tool, "", arguments
    return None, PROSE, {}


def last_question(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return str(message.get("content", "")).lower()
    return ""


def chunks(tool: str | None, text: str, arguments: dict[str, Any]) -> list[str]:
    """The reply as the provider streams it: deltas, a finish, then the sentinel."""
    if tool is not None:
        call = {
            "index": 0,
            "id": "call_e2e",
            "type": "function",
            "function": {"name": tool, "arguments": json.dumps(arguments)},
        }
        deltas = [{"role": "assistant", "tool_calls": [call]}]
        finish = "tool_calls"
    else:
        words = text.split(" ")
        deltas = [{"role": "assistant", "content": words[0]}] + [
            {"content": f" {word}"} for word in words[1:]
        ]
        finish = "stop"
    frames = [framed(delta, None) for delta in deltas]
    return [*frames, framed({}, finish), "data: [DONE]\n\n"]


def framed(delta: dict[str, Any], finish: str | None) -> str:
    return (
        "data: "
        + json.dumps(
            {
                "id": "e2e",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "fake",
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
            }
        )
        + "\n\n"
    )


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        """So whatever starts this can wait for it to be up."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(READY)))
        self.end_headers()
        self.wfile.write(READY)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for frame in chunks(*reply_to(body)):
            encoded = frame.encode()
            self.wfile.write(f"{len(encoded):x}\r\n".encode() + encoded + b"\r\n")
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet: the suite's output is what a run is read from."""


if __name__ == "__main__":
    print(f"fake model on http://{HOST}:{PORT}/v1")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
