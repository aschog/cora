from core.chat_engine import ChatEngine, build_context_block
from core.chat_model import ChatModel, ModelReply
from core.chunk import Chunk
from core.retrieval import RetrievedChunk
from fakes import FakeContextSource, ScriptedChatModel


def _make_engine(
    *,
    chat_model: ChatModel | None = None,
    knowledge_base: FakeContextSource | None = None,
    top_k: int = 3,
) -> ChatEngine:
    return ChatEngine(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text="ok")]),
        knowledge_base=knowledge_base or FakeContextSource(),
        top_k=top_k,
    )


def _retrieved(source: str, text: str = "t", score: float = 1.0) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=score
    )


def test_final_text_reply_becomes_the_answer() -> None:
    model = ScriptedChatModel([ModelReply(text="Hello!")])
    engine = _make_engine(chat_model=model)

    result = engine.answer("hi")

    assert result.answer == "Hello!"
    assert result.tool_results == ()


def test_answer_searches_the_knowledge_base_and_reports_unique_sources() -> None:
    kb = FakeContextSource(
        [_retrieved("a.txt"), _retrieved("a.txt"), _retrieved("b.txt")]
    )
    engine = _make_engine(knowledge_base=kb, top_k=5)

    result = engine.answer("question")

    assert kb.last_query == "question"
    assert kb.last_k == 5
    assert result.sources == ("a.txt", "b.txt")


def test_build_context_block_numbers_chunks_and_states_citation_rule() -> None:
    block = build_context_block(
        [_retrieved("a.txt", text="alpha"), _retrieved("b.txt", text="beta")]
    )

    assert block.index("[1]") < block.index("[2]")
    assert "alpha" in block and "a.txt" in block
    assert "beta" in block and "b.txt" in block
    assert "cite" in block.lower()
