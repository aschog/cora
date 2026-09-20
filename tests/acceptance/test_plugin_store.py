"""The outer test for the story: what a plugin keeps in its own store is still there in
another conversation, after the app that kept it is gone."""

from typing import Any

from app_builder import assembled
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension, Host
from cora.ports.plugin import ToolCall
from fakes import FakeMemory, ScriptedChatModel

KEEPING = "keep_a_count"
READING = "read_the_count"
MODULE = "fixture_plugins.counter"
NAME = "count"


def test_what_a_plugin_kept_outlives_the_conversation_that_kept_it(
    tmp_path: Any,
) -> None:
    file = str(tmp_path / "cora.sqlite")

    kept = _app(file, KEEPING)
    kept.agent.answer("Count it.", "first-conversation")
    del kept

    # A second app over the same file: another conversation, and the process the first
    # one ran in is as good as gone.
    read = _app(file, READING)
    read.agent.answer("What was counted?", "another-conversation")

    assert read.agent.answer("Again?", "a-third-conversation") is not None
    assert _said == ["1", "1"]


def test_what_a_plugin_keeps_is_not_what_cora_knows_about_the_user(
    tmp_path: Any,
) -> None:
    """Three lifetimes, and only one of them is the user's: what a plugin keeps for
    itself is not in the brief the model reads, and not in the rail that lists what
    cora knows."""
    from cora.adapters.sqlite_plugin_store import SqlitePluginStore

    memory = FakeMemory()
    model = ScriptedChatModel(
        [
            ModelReply(tool_calls=(ToolCall(name=KEEPING, arguments={}, call_id="c"),)),
            ModelReply(text="Done."),
        ]
    )
    app = assembled(
        chat_model=model,
        memory=memory,
        plugins=(Extension(module=MODULE, extend=_counting()),),
        store=SqlitePluginStore.at(str(tmp_path / "cora.sqlite")),
    )

    app.agent.answer("Count it.", "a-conversation")

    assert memory.recall() == ()
    assert model.last_messages is not None
    assert not any(message.content == "1" for message in model.last_messages)


_said: list[str] = []


def _app(file: str, tool: str) -> Any:
    from cora.adapters.sqlite_plugin_store import SqlitePluginStore

    return assembled(
        chat_model=ScriptedChatModel(
            [
                ModelReply(
                    tool_calls=(ToolCall(name=tool, arguments={}, call_id="c"),)
                ),
                ModelReply(text="Done."),
            ]
            * 3
        ),
        plugins=(Extension(module=MODULE, extend=_counting()),),
        store=SqlitePluginStore.at(file),
    )


def _counting() -> Any:
    def extend(cora: Host) -> None:
        def keep_a_count() -> str:
            assert cora.store is not None
            cora.store.keep(NAME, "1")
            return "kept"

        def read_the_count() -> str:
            assert cora.store is not None
            said = cora.store.read(NAME) or "nothing"
            _said.append(said)
            return said

        for name, run in ((KEEPING, keep_a_count), (READING, read_the_count)):
            cora.register_tool(
                name=name,
                description="The count this plugin keeps.",
                parameter_schema={"type": "object", "properties": {}},
                run=run,
            )

    return extend
