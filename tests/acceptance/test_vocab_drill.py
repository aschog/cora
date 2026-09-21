"""The outer test for the story: a word missed in one conversation is the word the drill
puts in the next one, because the schedule outlived the conversation that moved it.

Spaced, because that is what a schedule is for: a drill nobody spaced runs one pass and
keeps nothing past the conversation it ran in."""

from typing import Any

from app_builder import assembled
from cora.engine.plugin_registry import load_plugin
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, FakeFiles, ScriptedChatModel

FIELD = "vocab"
LIST = (
    "# English — Einheit 3\n\n"
    "| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n| Haus | house |\n"
)
MISSED = "Haus"
NEW = "Hilfe"


def test_a_word_missed_today_is_the_word_put_in_the_next_conversation(
    tmp_path: Any,
) -> None:
    from cora.adapters.sqlite_plugin_store import SqlitePluginStore

    store = SqlitePluginStore.at(str(tmp_path / "cora.sqlite"))
    # The list is the field's own file, as a screenshot kept on the page makes one.
    files = FakeFiles({(FIELD, "einheit-3.md"): LIST})
    # Today: a word is put, and the reader misses it.
    missing = ScriptedChatModel(
        [
            # The second word of the list, so that only a schedule that survived can
            # explain it being the one put first tomorrow.
            _calling("german_side", {"name": "einheit-3.md", "side": "left"}),
            _calling("next_word", {"spaced": True}),
            _calling("how_it_went", {"word": NEW, "right": True}),
            _calling("next_word", {"spaced": True}),
            _calling("how_it_went", {"word": MISSED, "right": False}),
            ModelReply(text="One right, one to come back to."),
        ]
    )
    _drilling(missing, store, files).agent.answer("Drill me.", "today", pin=FIELD)

    # Another conversation, another app over the same file: what the drill puts now is
    # the word that was missed, because the schedule is the plugin's own.
    asking = ScriptedChatModel(
        [_calling("next_word", {"spaced": True}), ModelReply(text="Here.")]
    )
    _drilling(asking, store, files).agent.answer(
        "Drill me again.", "tomorrow", pin=FIELD
    )

    assert asking.last_messages is not None
    put = [message for message in asking.last_messages if message.role == "tool"]
    assert any(MISSED in message.content for message in put)
    assert not any(NEW in message.content for message in put)


def _calling(tool: str, arguments: dict[str, Any]) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=tool, arguments=arguments, call_id=tool),)
    )


def _drilling(model: ScriptedChatModel, store: Any, files: FakeFiles) -> Any:
    return assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.vocab"),),
        conversations=FakeConversations(),
        store=store,
        files=files,
    )
