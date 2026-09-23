import importlib
import pathlib

from starlette.testclient import TestClient

from app_builder import assembled, shipped
from cora.adapters.directory_files import DirectoryFiles
from cora.app.assembly import App
from cora.domain.trace import ToolUse
from cora.frontends.react.api import api
from cora.ports.chat_model import ModelReply
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeMemory, ScriptedChatModel
from sse import frames

THREAD = "t1"
NOTE = "The maples turn in the second week of November."
FACT = "The user is vegetarian."
ASKED = "Which bodyweight should I treat as current?"
CITED = "They turn in November [1]."
SETTLED = "Then 75 kg it is."


def _call(tool: str, call_id: str, **arguments: object) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=tool, arguments=arguments, call_id=call_id),)
    )


def _uses(app: App) -> list[ToolUse]:
    result = app.agent.answer("Keep a note and read it back.", THREAD)
    return [step for step in result.trace if isinstance(step, ToolUse)]


def test_a_bare_cora_reads_writes_and_runs_in_its_field(tmp_path: pathlib.Path) -> None:
    shells = importlib.import_module("cora.adapters.subprocess_shell")
    model = ScriptedChatModel(
        [
            _call("write", "w1", name="note.md", text=NOTE),
            _call("read", "r1", name="note.md"),
            _call("bash", "b1", command="ls"),
            ModelReply(text="Kept and read back."),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(),
        searching=False,
        files=DirectoryFiles.at(str(tmp_path)),
        shell=shells.SubprocessShell.at(str(tmp_path)),
    )

    written, read, listed = _uses(app)

    assert model.last_tools is not None
    assert {tool.name for tool in model.last_tools} == {"read", "write", "bash"}
    assert (tmp_path / DEFAULT_SCOPE / "note.md").read_text() == NOTE
    assert NOTE in read.detail
    assert "note.md" in listed.detail
    assert not any(step.failed for step in (written, read, listed))
    assert app.agent.pending(THREAD) is None, "nothing waited for approval"


def _upload(reader: TestClient, name: str, data: bytes) -> None:
    added = reader.post("/api/documents", files={"file": (name, data, "text/plain")})
    assert added.status_code == 200


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


def test_the_three_plugins_bring_back_search_asking_and_memory(
    tmp_path: pathlib.Path,
) -> None:
    memory = FakeMemory()
    model = ScriptedChatModel(
        [
            _call("search_documents", "s1", query="maples"),
            ModelReply(text=CITED),
            _call(
                "ask_user",
                "a1",
                question=ASKED,
                options=[{"label": "77 kg"}, {"label": "75 kg"}],
            ),
            ModelReply(text=SETTLED),
            _call("remember", "m1", fact=FACT),
            ModelReply(text="Noted."),
        ]
    )
    app = assembled(
        chat_model=model,
        memory=memory,
        conversations=FakeConversations(),
        files=DirectoryFiles.at(str(tmp_path)),
        searching=False,
        plugins=shipped("ask", "memory", "documents"),
    )

    with TestClient(api(app)) as reader:
        _upload(reader, "maples.md", NOTE.encode())
        assert (tmp_path / DEFAULT_SCOPE / "maples.md").is_file()

        cited = app.agent.answer("When do the maples turn?", THREAD)
        assert cited.answer == CITED
        assert [each.document for each in cited.citations] == ["maples.md"]

        asked = reader.post(
            "/api/ask", json={"question": "Which weight?", "thread_id": "t2"}
        )
        [paused] = _of(asked.text, "paused")
        assert paused["card"]["prompt"] == ASKED
        settled = reader.post("/api/resume", json={"thread_id": "t2", "answer": "1"})
        [turn] = _of(settled.text, "turn")
        assert turn["answer"] == SETTLED
        assert model.last_messages is not None
        assert any("75 kg" in message.content for message in model.last_messages)

        app.agent.answer("Remember that I am vegetarian.", "t3")
        assert [fact.text for fact in memory.recall()] == [FACT]

    later = ScriptedChatModel([ModelReply(text="Lentils.")])
    again = assembled(chat_model=later, memory=memory, plugins=shipped("memory"))
    again.agent.answer("What should I eat?", "t4")
    assert later.last_messages is not None
    assert FACT in later.last_messages[0].content
