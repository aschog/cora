import pathlib

import cora.plugins.vocab as vocab
from cora.plugins.vocab import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import INSTRUCTIONS as SAYS
from cora.ports.host import PAGE
from fakes import host_for


def test_the_field_is_a_voice_and_a_page_and_nothing_else() -> None:
    """A field that answers from its lists and opens on the page that writes them:
    searching them is cora's own tool, so the plugin registers none."""
    host = host_for("cora.plugins.vocab")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (SAYS, SCOPE),
        (PAGE, SCOPE),
    ]


def test_the_instructions_say_what_the_field_answers_from() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "vocabular" in instructions
    assert "cite" in instructions


def test_the_page_is_the_directory_shipped_beside_the_module() -> None:
    """The page is files, so where it is registered from is where the wheel puts it."""
    host = host_for("cora.plugins.vocab")

    extend(host)

    [page] = [entry for entry in host.registered if entry.kind == PAGE]
    assert page.scope == SCOPE
    assert page.value == pathlib.Path(vocab.__file__).parent / "page"
    assert (page.value / "index.html").is_file()
