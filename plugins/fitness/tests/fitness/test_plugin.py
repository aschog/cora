import pathlib
import re
import urllib.parse

import cora.plugins.fitness as fitness
from cora.plugins.fitness import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import HANDLER, PAGE, SCREENING, TOOL
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the domain, the
    tools that must do its arithmetic, and where it stops."""
    instructions = INSTRUCTIONS.lower()

    assert "coach" in instructions
    assert "cite" in instructions
    assert "tool" in instructions
    assert "medical" in instructions


def test_the_instructions_carry_the_caution_the_screen_stopped_refusing_for() -> None:
    """`refuse_medical` lets a named condition through to be answered, so the caution
    that answer needs has to come from somewhere: only the model writes it, and only if
    the domain says so."""
    instructions = INSTRUCTIONS.lower()

    assert "condition" in instructions
    assert "doctor" in instructions


def test_the_coaching_is_scoped_and_the_medical_screen_is_not() -> None:
    """One plugin under two lifetimes: the persona and the calculators belong to a turn
    asking as a coach, and the medical filter holds wherever the question was asked."""
    host = host_for("cora.plugins.fitness")

    extend(host)

    under = [(entry.kind, entry.scope) for entry in host.registered]
    assert under.count((TOOL, SCOPE)) == 3
    assert under.count((SAYS, SCOPE)) == 1
    assert under.count((HANDLER, None)) == 1
    [screen] = [entry for entry in host.registered if entry.kind == HANDLER]
    assert screen.value.event == SCREENING


def test_the_field_is_brought_a_trainer_shipped_beside_the_module() -> None:
    """The page is files, so where it is registered from is where the wheel puts it."""
    host = host_for("cora.plugins.fitness")

    extend(host)

    [page] = [entry for entry in host.registered if entry.kind == PAGE]
    assert page.scope == SCOPE
    assert page.value == pathlib.Path(fitness.__file__).parent / "page"
    assert (page.value / "index.html").is_file()


REACHES = frozenset(
    {
        # the plan: a published sheet, read on load and fallen back from when it is
        # not there. It answers any origin, so the page asks rather than cora asking
        "docs.google.com",
        # the thumbnail of an exercise clip, asked for as the plan is drawn
        "i.ytimg.com",
        # the clip itself, played in the frame, from the host that sets no cookie
        # until it is
        "www.youtube-nocookie.com",
        # the pose runtime and its model, fetched only when tracking is turned on
        "cdn.jsdelivr.net",
        "storage.googleapis.com",
    }
)


def test_the_trainer_reaches_only_the_hosts_it_is_said_to() -> None:
    """The page is the plugin's own code in the reader's browser, so what it may ask for
    is a list somebody wrote down rather than a handful of names a test happens to
    check. Every address in the file, by host, against that list — so a fifth one fails
    here and is either named or taken out."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    reached = {
        urllib.parse.urlparse(found).hostname or ""
        for found in re.findall(r"https?://[^\s\'\"<>)]+", drawn)
    }

    assert reached == REACHES


def test_the_trainer_asks_for_its_plan_and_hands_the_workout_to_cora() -> None:
    """Two things it fetches and no third: the plan it trains from, which is read, and
    the workout it finished, which is the one thing it sends anywhere — and that goes to
    cora. A log server of its own, a watch listener, a second place to write: each would
    be an answer to a problem cora answers."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    asked = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)", drawn)
    posted = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)[^)]*method:\s*'POST'", drawn)

    assert sorted(set(asked)) == ["SHEET_CSV", "UPLOAD"]
    assert posted == ["UPLOAD"]
    assert "const UPLOAD = '/api/documents'" in drawn


def test_the_shipped_plan_is_written_in_the_language_the_coach_answers_in() -> None:
    """The workout becomes a document this field is searched over, and the persona
    above answers in English — a plan named in another language is a log the coach
    retrieves against poorly, in the one field where the reader asks about it."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    named = re.findall(r'n:"([^"]*)"', drawn)

    assert named, "the page ships no plan"
    assert all(each.isascii() for each in named), [
        each for each in named if not each.isascii()
    ]
