import json
import pathlib
import re
import urllib.parse

import cora.plugins.fitness as fitness
from cora.plugins.fitness import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import HANDLER, PAGE, SCREENING, TOOL
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_instructions_state_the_domains_own_business() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "coach" in instructions
    assert "cite" in instructions
    assert "tool" in instructions
    assert "medical" in instructions


def test_the_instructions_carry_the_caution_the_screen_stopped_refusing_for() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "condition" in instructions
    assert "doctor" in instructions


def test_the_coaching_is_scoped_and_the_medical_screen_is_not() -> None:
    host = host_for("cora.plugins.fitness")

    extend(host)

    under = [(entry.kind, entry.scope) for entry in host.registered]
    assert under.count((TOOL, SCOPE)) == 4
    assert under.count((SAYS, SCOPE)) == 1
    assert under.count((HANDLER, None)) == 1
    [screen] = [entry for entry in host.registered if entry.kind == HANDLER]
    assert screen.value.event == SCREENING


def test_the_field_offers_the_log_read_back_and_it_changes_nothing() -> None:
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
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    reached = {
        urllib.parse.urlparse(found).hostname or ""
        for found in re.findall(r"https?://[^\s\'\"<>)]+", drawn)
    }

    assert reached == REACHES


def test_the_trainer_asks_for_its_plan_its_field_and_hands_the_workout_over() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    asked = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)", drawn)
    posted = re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)[^)]*method:\s*'POST'", drawn)

    assert sorted(set(asked)) == ["HELD", "LISTED", "NOTICE", "SHEET_CSV", "UPLOAD"]
    assert posted == ["UPLOAD"]
    assert "const UPLOAD = '/api/documents'" in drawn
    assert "'/api/scopes/' + encodeURIComponent(FIELD) + '/notice'" in drawn


def test_the_trainer_carries_nothing_between_browsers() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert 'id="exp"' not in drawn
    assert 'id="imp"' not in drawn
    assert 'id="box"' not in drawn
    assert "clipboard" not in drawn


def test_the_trainer_asks_for_no_pulse_and_writes_no_heart_line() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "♥" not in drawn
    assert "bpm" not in drawn


def test_the_shipped_plan_is_written_in_the_language_the_coach_answers_in() -> None:
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
    packaged = pathlib.Path(fitness.__file__).parent

    assert (WATCH / "app.json").is_file()
    assert WATCH.is_dir() and packaged not in WATCH.parents
    assert not list(packaged.rglob("data-widget"))


def test_the_watch_writes_the_field_notice_when_its_screen_opens() -> None:
    drawn = _widget()

    opened = re.search(r"onInit\(\)\s*\{(.*?)\n  \}", drawn, re.S)

    assert opened, "the widget says nothing at onInit"
    assert "this.write(RUNNING)" in opened.group(1)


def test_a_second_workout_can_be_finished_from_the_wrist_too() -> None:
    drawn = _widget()

    opened = re.search(r"onInit\(\)\s*\{(.*?)\n  \}", drawn, re.S)

    assert opened and "this.state.done = false" in opened.group(1)


def test_a_tap_cora_never_took_can_be_tapped_again() -> None:
    drawn = _widget()

    assert re.search(r"this\.write\(FINISHED\)\s*\.then\(", drawn)
    assert "this.state.done = false" in drawn.split("finish()")[-1]


def test_the_watch_finishes_the_workout_from_a_tap_and_from_nothing_else() -> None:
    drawn = _widget()

    assert drawn.count("click_func") == 1
    assert "click_func: () => this.finish()" in drawn
    assert drawn.count("this.finish()") == 1, "one caller, whatever it is bound to"
    assert re.search(r"finish\(\)\s*\{.*?this\.write\(FINISHED\)", drawn, re.S)
    assert drawn.count("this.write(") == 2, (
        "it writes at onInit and at the tap, no more"
    )


def test_the_watch_writes_the_notice_and_reaches_nothing_else() -> None:
    drawn = _widget()

    assert re.findall(r"httpRequest\(\{[^}]*url: (\w+)", drawn) == ["NOTICE"]
    assert "import { NOTICE } from '../config'" in drawn
    assert not re.search(r"https?://", drawn)


def test_the_watch_asks_for_no_permission() -> None:
    manifest = json.loads((WATCH / "app.json").read_text())

    assert manifest["permissions"] == []
    assert "heart" not in _widget().lower()


def test_the_trainer_keeps_no_history_and_reads_the_fields_own() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "save('kb.hist'" not in drawn
    assert "load('kb.hist'" not in drawn
    # the one mention left is the clearing of what an earlier page kept
    assert drawn.count("kb.hist") == 1
    assert "localStorage.removeItem('kb.hist')" in drawn
    assert "'/api/documents?scope=' + encodeURIComponent(FIELD)" in drawn
    assert "'/api/documents/' + encodeURIComponent(FIELD) + '/'" in drawn


def test_the_trainer_names_a_save_for_its_moment_and_then_its_workout() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    naming = re.search(r"function moment\(\)\{(.*?)\n\}", drawn, re.S)

    assert naming, "the page has no moment()"
    assert (
        "`${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())}"
        "-${two(d.getHours())}-${two(d.getMinutes())}-${two(d.getSeconds())}`"
    ) in naming.group(1)
    assert "WORKOUT" in naming.group(1), "the workout is named behind the moment"
    assert drawn.count("moment()") == 2, "defined once, and called once at the save"
    assert "today()" not in drawn


def test_the_trainer_takes_the_workouts_name_off_the_sheet_and_writes_it_first() -> (
    None
):
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "function workoutName(" in drawn
    assert "workoutName(r.headers.get('content-disposition'))" in drawn
    assert "save('kb.workout'" in drawn
    assert "load('kb.workout'" in drawn
    assert "(WORKOUT ? WORKOUT + '\\n\\n' : '') + sessionText(" in drawn


def test_a_row_carries_its_number_and_its_name_and_no_readout() -> None:
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
    assert re.search(
        r"const anySet = PLAN\.some\(.*\n\s*finishEl\.disabled = !anySet", drawn
    )


def test_a_save_cora_took_says_nothing_on_the_strip() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "'Saved to '" not in drawn
    assert "Not saved to cora" in drawn


def test_the_finish_reads_where_the_workout_stands() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    assert "No sets logged yet" in drawn
    assert "CHECK + ' Saved'" in drawn
    assert "saved = true" in drawn
    assert "saved = false" in drawn


def test_the_trainer_places_an_exercises_name_as_text() -> None:
    drawn = (pathlib.Path(fitness.__file__).parent / "page" / "index.html").read_text()

    named = [
        found
        for found in re.findall(r"\$\{([^{}]*)\}", drawn)
        if re.search(r"\b\w+\.n\b", found)
    ]

    assert named, "the page interpolates no name at all"
    assert [found for found in named if "esc(" not in found] == []
