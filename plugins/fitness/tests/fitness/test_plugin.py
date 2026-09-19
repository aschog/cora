import json
import pathlib
import re
import urllib.parse

import pytest

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
    assert under.count((TOOL, SCOPE)) == 4
    assert under.count((SAYS, SCOPE)) == 1
    assert under.count((HANDLER, None)) == 1
    [screen] = [entry for entry in host.registered if entry.kind == HANDLER]
    assert screen.value.event == SCREENING


def test_the_field_offers_the_log_read_back_and_it_changes_nothing() -> None:
    """The fourth tool is the one that closes over the host: it reads the field the
    turn runs in, so it is registered in `extend` rather than kept in `TOOLS`."""
    host = host_for("cora.plugins.fitness")

    extend(host)

    [listing] = [
        entry
        for entry in host.registered
        if entry.kind == TOOL and entry.value.name == "list_workouts"
    ]
    assert listing.scope == SCOPE
    assert not listing.value.effect
    assert set(listing.value.parameter_schema["properties"]) == {
        "exercise",
        "since",
        "detail",
    }


def test_the_brief_routes_the_log_to_the_listing_and_the_rest_to_search() -> None:
    """Search ranks by wording and cuts at k, so a question about what was trained
    goes to the tool that lists every session — and the brief is what sends it there."""
    instructions = INSTRUCTIONS.lower()

    assert "list_workouts" in instructions
    assert "search" in instructions
    # relayed as it is: the tool renders, the model does not translate or tabulate
    assert "as it is" in instructions
    assert "translat" in instructions
    assert "detail" in instructions
    # and nothing of the model's own about what the log holds or lacks
    assert "holds or lacks" in instructions


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
    """Three things it fetches and no fourth: the plan it trains from, the field's
    notice, which says what the wrist is doing, and the workout it finished — which is
    the one thing it sends anywhere, and goes to cora. A log server of its own, a watch
    listener, a second place to write: each would answer a problem cora answers."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    asked = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)", drawn)
    posted = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)[^)]*method:\s*'POST'", drawn)

    assert sorted(set(asked)) == ["NOTICE", "SHEET_CSV", "UPLOAD"]
    assert posted == ["UPLOAD"]
    assert "const UPLOAD = '/api/documents'" in drawn
    assert "'/api/scopes/' + encodeURIComponent(FIELD) + '/notice'" in drawn


def test_the_trainer_asks_for_no_pulse_and_writes_no_heart_line() -> None:
    """The lifter asked for a clock and not a heartbeat. Nothing writes a pulse once the
    sensor is gone, and a heart line reading a dash is worse than no heart line."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "♥" not in drawn
    assert "bpm" not in drawn


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


WATCH = pathlib.Path(fitness.__file__).parents[4] / "watch"


def _widget() -> str:
    return (WATCH / "data-widget" / "index.js").read_text()


def test_the_watch_app_ships_outside_the_module_a_wheel_carries() -> None:
    """The extension is JavaScript for a watch, built by the Zepp tooling and installed
    by hand. Under `src` it would ride in the wheel as the page rightly does, and cora
    would serve a build input at an address."""
    packaged = pathlib.Path(fitness.__file__).parent

    assert (WATCH / "app.json").is_file()
    assert WATCH.is_dir() and packaged not in WATCH.parents
    assert not list(packaged.rglob("data-widget"))


def test_the_watch_writes_the_field_notice_when_its_screen_opens() -> None:
    """onInit and nothing later: the workout app creates this page when the workout
    starts, and that is the moment the trainer's workout has to start from."""
    drawn = _widget()

    opened = re.search(r"onInit\(\)\s*\{(.*?)\n  \}", drawn, re.S)

    assert opened, "the widget says nothing at onInit"
    assert "this.write(RUNNING)" in opened.group(1)


def test_a_second_workout_can_be_finished_from_the_wrist_too() -> None:
    """`state` is one object for the life of the app, not one per page — so a flag left
    true by the first workout's tap is a second workout whose control does nothing. It
    is reset where a workout begins, which is where its screen is created."""
    drawn = _widget()

    opened = re.search(r"onInit\(\)\s*\{(.*?)\n  \}", drawn, re.S)

    assert opened and "this.state.done = false" in opened.group(1)


def test_a_tap_cora_never_took_can_be_tapped_again() -> None:
    """The one failure the lifter is standing there for: the phone could not reach cora,
    and a control spent on a write that never landed is a workout they cannot save
    without starting the whole thing again."""
    drawn = _widget()

    assert re.search(r"this\.write\(FINISHED\)\s*\.then\(", drawn)
    assert "this.state.done = false" in drawn.split("finish()")[-1]


def test_the_watch_finishes_the_workout_from_a_tap_and_from_nothing_else() -> None:
    """The end of a system workout reaches nothing, so the finish is a click. One
    handler, on the one control — a second way in would be a second way to save a
    workout by accident."""
    drawn = _widget()

    assert drawn.count("click_func") == 1
    assert "click_func: () => this.finish()" in drawn
    assert drawn.count("this.finish()") == 1, "one caller, whatever it is bound to"
    assert re.search(r"finish\(\)\s*\{.*?this\.write\(FINISHED\)", drawn, re.S)
    assert drawn.count("this.write(") == 2, (
        "it writes at onInit and at the tap, no more"
    )


def test_the_watch_writes_the_notice_and_reaches_nothing_else() -> None:
    """One address, and it is the one the build wrote. A host spelled into the source
    is a watch that keeps writing wherever it was built for."""
    drawn = _widget()

    assert re.findall(r"httpRequest\(\{[^}]*url: (\w+)", drawn) == ["NOTICE"]
    assert "import { NOTICE } from '../config'" in drawn
    assert not re.search(r"https?://", drawn)


def test_the_watch_asks_for_no_permission() -> None:
    """The lifter wanted a clock, not a heartbeat — and a workout extension that reads
    the pulse is one the wearer is asked to allow."""
    manifest = json.loads((WATCH / "app.json").read_text())

    assert manifest["permissions"] == []
    assert "heart" not in _widget().lower()


def test_the_trainer_names_a_save_for_its_moment_day_first() -> None:
    """One entry in the rail per save, and a day's saves in the order they happened:
    the name carries the time behind the day, in the lifter's own clock."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    naming = re.search(r"function moment\(\)\{(.*?)\n\}", drawn, re.S)

    assert naming, "the page has no moment()"
    assert (
        "`${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}"
        "-${two(d.getHours())}-${two(d.getMinutes())}-${two(d.getSeconds())}.md`"
    ) in naming.group(1)
    assert drawn.count("moment()") == 2, "defined once, and called once at the save"
    assert "today()" not in drawn


def test_the_trainer_takes_the_workouts_name_off_the_sheet_and_writes_it_first() -> (
    None
):
    """The tab's name is not in the CSV's cells but in the export's filename header,
    which Google lets any origin read: the page reads it there, keeps it beside the
    plan for a save made offline, and a save opens with it."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "function workoutName(" in drawn
    assert "workoutName(r.headers.get('content-disposition'))" in drawn
    assert "save('kb.workout'" in drawn
    assert "load('kb.workout'" in drawn
    assert "(WORKOUT ? WORKOUT + '\\n\\n' : '') + sessionText(" in drawn


def test_a_row_carries_its_number_and_its_name_and_no_readout() -> None:
    """The count and the weight live in the sets panel, where they are worked; a row is
    the exercise, and nothing beside its name."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert 'class="st"' not in drawn
    assert ".row .st" not in drawn


def test_the_weight_moves_one_kilogram_a_tap_and_never_below_one() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert 'data-w="-1"' in drawn
    assert 'data-w="1"' in drawn
    assert "Math.max(1, s.w + (+w.dataset.w))" in drawn


def test_the_finish_is_named_so_and_offered_only_once_a_set_is_logged() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "Save &amp; finish" not in drawn
    assert re.search(r'id="finish">.*?</svg> Finish</button>', drawn)
    assert re.search(r"finishEl\.disabled\s*=\s*!PLAN\.some\(", drawn)


def test_a_save_cora_took_says_nothing_on_the_strip() -> None:
    """A refused save still says so, and the watch's line stays: what goes is the line
    for a save that worked, which the History and the rail already say."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "'Saved to '" not in drawn
    assert "Not saved to cora" in drawn


@pytest.mark.xfail(strict=True, reason="the button says Finish whatever it waits for")
def test_the_finish_reads_where_the_workout_stands() -> None:
    """Three faces on one control: nothing logged yet, finish, and saved — the last
    held until a set is logged again."""
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "No sets logged yet" in drawn
    assert "CHECK + ' Saved'" in drawn
    assert "saved = true" in drawn
    assert "saved = false" in drawn
