import re

import workspace
from cora.domain.citations import CITATION_RUN

TS_LITERAL = re.compile(r"const CITATION_RUN = /(?P<pattern>.+)/g")
CLIENT = workspace.ROOT / "frontends" / "react" / "ui" / "src" / "answer.ts"


def test_the_page_resolves_a_citation_by_the_domain_s_own_rule() -> None:
    found = TS_LITERAL.search(CLIENT.read_text())

    assert found is not None, f"no citation rule found in {CLIENT.name}"
    assert found["pattern"] == CITATION_RUN.pattern
