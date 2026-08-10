import re

import pytest
from playwright.sync_api import Page, expect

from app_page import ask, messages, open_expander, upload
from stub_llm import StubLlm

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(180)]

CITATION = re.compile(r"\[(\d+)\]")


def test_an_answer_cites_only_sources_it_lists(app: Page, stub: StubLlm) -> None:
    upload(app, "protein.md", b"# Protein\n\nAim for ~1.6 g of protein per kg per day.")
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
