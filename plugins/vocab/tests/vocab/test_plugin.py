import pathlib
import re
import urllib.parse

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


REACHES = frozenset(
    {
        # the reading: the script, its WebAssembly core and every language's trained
        # data, all pinned on one host and fetched the first time a screenshot is read
        "cdn.jsdelivr.net",
    }
)


def test_the_page_reaches_only_the_hosts_it_is_said_to() -> None:
    """The page is the plugin's own code in the reader's browser, so what it may ask for
    is a list somebody wrote down rather than a handful of names a test happens to
    check. Every address in the file, by host, against that list — so a second one fails
    here and is either named or taken out."""
    drawn = (pathlib.Path(vocab.__file__).parent / "page" / "index.html").read_text()

    reached = {
        urllib.parse.urlparse(found).hostname or ""
        for found in re.findall(r"https?://[^\s\'\"<>)]+", drawn)
    }

    assert reached == REACHES


def test_the_page_sends_the_list_to_cora_and_nowhere_else() -> None:
    """The one thing it sends anywhere is the list the reader corrected, and it goes to
    the field the page is served under. The screenshot is read where it was dropped, so
    no image is posted at all."""
    drawn = (pathlib.Path(vocab.__file__).parent / "page" / "index.html").read_text()

    asked = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)", drawn)

    assert sorted(set(asked)) == ["UPLOAD"]
