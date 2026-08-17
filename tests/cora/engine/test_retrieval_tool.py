from cora.domain.chunk import Chunk
from cora.domain.citations import CitableHits
from cora.engine.retrieval_tool import (
    EMPTY_STORE,
    SEARCH_TOOL_NAME,
    search_tool,
)
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.plugin import ToolCall
from cora.ports.retrieval import RetrievedChunk
from fakes import FakeContextSource


def _hit(source: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(text=text, source=source, index=0, offset=0), score=1.0
    )


def test_the_tool_searches_its_source_and_returns_the_hits_as_citable() -> None:
    hits = [_hit("note.md", "protein builds muscle")]
    source = FakeContextSource(hits)
    tool = search_tool(source, top_k=4)

    payload = tool.run(query="protein")

    assert source.last_query == "protein"
    assert source.last_k == 4
    assert payload == CitableHits(hits, nothing=EMPTY_STORE)


def test_a_search_of_an_empty_store_says_the_store_is_empty() -> None:
    """ "No matching documents" reads as "your documents don't cover this" and is how an
    empty store used to be reported — so a model that had searched went ahead and
    answered. The tool states the fact; what to do about it is a rule in the brief,
    because a tool result reaches the model labelled as data never to be followed."""
    tool = search_tool(FakeContextSource([]), top_k=4)

    payload = tool.run(query="protein")

    assert payload.register(known=()).text == EMPTY_STORE.told
    assert payload.summary == EMPTY_STORE.shown


def test_a_call_without_a_query_comes_back_as_an_invalid_arguments_error() -> None:
    runtime = ToolRuntime(tools=(search_tool(FakeContextSource(), top_k=4),))

    result = runtime.execute(
        ToolCall(name=SEARCH_TOOL_NAME, arguments={}, call_id="call-1")
    )

    assert result.payload is None
    assert result.error is not None
    assert "invalid arguments" in result.error
