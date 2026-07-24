import pytest

from cora.composition import assemble
from core.chat_engine import ChatEngine
from core.chat_model import ModelReply
from core.errors import InputRejectedError
from core.plugin import Plugin
from fakes import FakeEmbedder, FakeRetriever, ScriptedChatModel
from fixture_plugins import make_plugin


def _assemble(
    plugin: Plugin,
    *,
    chat_model: ScriptedChatModel | None = None,
    retriever: FakeRetriever | None = None,
) -> ChatEngine:
    return assemble(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        embedder=FakeEmbedder(),
        retriever=retriever or FakeRetriever(),
        plugin=plugin,
    )


def test_assemble_answers_a_happy_path_question() -> None:
    engine = _assemble(
        make_plugin(), chat_model=ScriptedChatModel([ModelReply(text="42")])
    )

    result = engine.answer("What is the answer?")

    assert result.answer == "42"


def test_assemble_seeds_plugin_docs_into_the_knowledge_base() -> None:
    plugin = make_plugin(seed_docs=(("note.md", b"protein supports muscle growth"),))
    retriever = FakeRetriever()

    _assemble(plugin, retriever=retriever)

    assert "note.md" in retriever.sources()


class _RejectBanned:
    def apply(self, user_input: str) -> None:
        if "banned" in user_input:
            raise InputRejectedError("No banned words, please.")


def test_assemble_chains_core_and_plugin_validation_rules() -> None:
    engine = _assemble(make_plugin(validation_rules=(_RejectBanned(),)))

    with pytest.raises(InputRejectedError):
        engine.answer("   ")  # core rule: empty input

    with pytest.raises(InputRejectedError):
        engine.answer("a banned word")  # plugin rule
