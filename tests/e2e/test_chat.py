import re

import pytest
from playwright.sync_api import Page, expect

from app_page import ask, messages, open_expander, upload
from cora.core.services.retrieval_tool import SEARCH_TOOL_NAME
from stub_llm import StubLlm

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]

CITATION = re.compile(r"\[(\d+)\]")


TRACE = "How I got there"


def test_the_trace_names_the_search_its_query_and_what_it_returned(
    app: Page, stub: StubLlm
) -> None:
    upload(app, "protein.md", b"# Protein\n\nAim for ~1.6 g of protein per kg per day.")
    stub.script_tool_call(SEARCH_TOOL_NAME, {"query": "protein"})
    stub.script_answer("Protein supports recovery [1].")

    ask(app, "How much protein should I eat?")
    stub.script_tool_call(SEARCH_TOOL_NAME, {"query": "creatine"})
    stub.script_answer("Creatine is well studied [1].")
    ask(app, "What about creatine?")

    first = open_expander(messages(app).nth(1), TRACE).inner_text()
    assert f'{SEARCH_TOOL_NAME}(query="protein")' in first
    assert "passage from protein.md" in first

    last = open_expander(messages(app).last, TRACE).inner_text()
    assert f'{SEARCH_TOOL_NAME}(query="creatine")' in last
    assert "protein" not in last.split("→")[0], "each turn shows its own steps"


def test_an_answer_cites_only_sources_it_lists(app: Page, stub: StubLlm) -> None:
    upload(app, "protein.md", b"# Protein\n\nAim for ~1.6 g of protein per kg per day.")
    stub.script_tool_call(SEARCH_TOOL_NAME, {"query": "protein"})
    stub.script_answer("Protein supports recovery [1].")

    ask(app, "How much protein should I eat?")

    answer = messages(app).last
    expect(answer).to_contain_text("Protein supports recovery")
    cited = set(CITATION.findall(answer.inner_text()))
    listed = set(CITATION.findall(open_expander(app, "Sources").inner_text()))
    assert cited, "the answer cited nothing, so this spec proved nothing"
    assert cited <= listed, (
        f"cited {sorted(cited)} but only {sorted(listed)} are listed"
    )
