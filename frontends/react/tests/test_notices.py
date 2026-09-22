"""A field's notice: the one live value cora holds for a field, written by whatever is
beside the reader and read by that field's page."""

import json
import pathlib
import time
from typing import Any

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App, LiveApp
from cora.frontends.react.api import api
from cora.ports.host import DEFAULT_SCOPE, Extension, Host

FIELD = "training"
OTHER = "travel"
WHERE = f"/api/scopes/{FIELD}/notice"

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("You coach lifting.", scope="training")
"""


def _fields(*named: str, **overrides: Any) -> App:
    def extend(cora: Host) -> None:
        for field in named:
            cora.register_instructions(f"You are the {field}.", scope=field)

    return assembled(
        plugins=(Extension(module="fixture_plugins.fields", extend=extend),),
        **overrides,
    )


def _reader(*named: str) -> TestClient:
    return TestClient(api(_fields(*named or (FIELD,))))


def test_a_notice_written_to_a_field_is_read_back_by_whoever_asks_next() -> None:
    """The whole of it: something beside the reader says what it is doing, cora holds
    the last such word per field, and the field's page reads it stamped with the time
    cora heard it rather than a time the writer claimed."""
    reader = _reader()
    before = int(time.time() * 1000)

    written = reader.put(WHERE, json={"doing": "a workout", "since": "the writer says"})

    assert written.status_code == 200
    held = reader.get(WHERE)
    assert held.status_code == 200
    assert held.json()["notice"] == {"doing": "a workout", "since": "the writer says"}
    assert before <= held.json()["at"] <= int(time.time() * 1000)


def test_a_field_nobody_wrote_to_answers_that_it_has_no_notice() -> None:
    before = int(time.time() * 1000)
    held = _reader().get(WHERE)

    assert held.status_code == 200
    assert held.json()["notice"] is None
    # Cora's clock comes with every read, so a page on a second machine judges an
    # arrival against cora's terms rather than across the two.
    assert before <= held.json()["now"] <= int(time.time() * 1000)


def test_a_second_notice_replaces_the_first_rather_than_joining_it() -> None:
    reader = _reader()
    reader.put(WHERE, json={"doing": "a workout", "sets": 3})

    reader.put(WHERE, json={"doing": "resting"})

    assert reader.get(WHERE).json()["notice"] == {"doing": "resting"}


def test_each_field_answers_the_notice_written_to_it() -> None:
    reader = _reader(FIELD, OTHER)
    reader.put(WHERE, json={"doing": "a workout"})

    reader.put(f"/api/scopes/{OTHER}/notice", json={"doing": "a flight"})

    assert reader.get(WHERE).json()["notice"] == {"doing": "a workout"}
    assert reader.get(f"/api/scopes/{OTHER}/notice").json()["notice"] == {
        "doing": "a flight"
    }


def test_the_field_cora_ships_keeps_a_notice_like_any_other() -> None:
    reader = _reader()

    reader.put(f"/api/scopes/{DEFAULT_SCOPE}/notice", json={"doing": "nothing"})

    assert reader.get(f"/api/scopes/{DEFAULT_SCOPE}/notice").json()["notice"] == {
        "doing": "nothing"
    }


def test_the_arrival_a_notice_carries_is_the_one_cora_wrote() -> None:
    reader = _reader()

    before = int(time.time() * 1000)
    reader.put(WHERE, json={"doing": "a workout"})
    after = int(time.time() * 1000)

    assert before <= reader.get(WHERE).json()["at"] <= after


def test_a_writer_stating_its_own_time_is_stamped_with_coras() -> None:
    """A watch, a sensor or a phone has a clock of its own and no reason to share
    cora's, so the one time anything can reason about is the one cora wrote."""
    reader = _reader()

    reader.put(WHERE, json={"at": 5, "doing": "a workout"})

    held = reader.get(WHERE).json()
    assert held["at"] > 5
    assert held["notice"]["at"] == 5


def test_a_notice_written_to_a_name_that_is_no_field_is_refused() -> None:
    reader = _reader()

    refused = reader.put("/api/scopes/gardening/notice", json={"doing": "a workout"})

    assert refused.status_code == 400
    assert FIELD in refused.json()["error"]
    assert "gardening" in refused.json()["error"]


def test_asking_for_the_notice_of_a_name_that_is_no_field_is_refused() -> None:
    reader = _reader()

    refused = reader.get("/api/scopes/gardening/notice")

    assert refused.status_code == 400
    assert reader.get("/api/scopes").status_code == 200


def _dropped(folder: pathlib.Path) -> pathlib.Path:
    trainer = folder / "trainer"
    trainer.mkdir()
    (trainer / "__init__.py").write_text(DROPPED)
    return trainer


def _live(folder: pathlib.Path) -> TestClient:
    return TestClient(
        api(
            LiveApp(
                named=(),
                folder=folder,
                compose=lambda loaded: assembled(plugins=loaded),
            )
        )
    )


def test_a_field_brought_by_a_dropped_plugin_takes_a_notice(
    tmp_path: pathlib.Path,
) -> None:
    reader = _live(tmp_path)
    assert reader.put(WHERE, json={"doing": "a workout"}).status_code == 400

    _dropped(tmp_path)

    assert reader.put(WHERE, json={"doing": "a workout"}).status_code == 200
    assert reader.get(WHERE).json()["notice"] == {"doing": "a workout"}


def test_the_notice_of_a_field_whose_plugin_went_away_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    trainer = _dropped(tmp_path)
    reader = _live(tmp_path)
    reader.put(WHERE, json={"doing": "a workout"})

    (trainer / "__init__.py").unlink()

    assert reader.get(WHERE).status_code == 400


def test_a_notice_past_the_ceiling_is_refused_and_the_held_one_still_answers() -> None:
    reader = _reader()
    reader.put(WHERE, json={"doing": "a workout"})

    refused = reader.put(WHERE, json={"doing": "x" * (8 * 1024)})

    assert refused.status_code == 413
    assert reader.get(WHERE).json()["notice"] == {"doing": "a workout"}


def test_a_body_that_is_not_a_json_object_is_refused() -> None:
    reader = _reader()
    reader.put(WHERE, json={"doing": "a workout"})

    for body in (b"[1, 2]", b'"a workout"', b"not json at all"):
        refused = reader.put(WHERE, content=body)
        assert refused.status_code == 400, body

    assert reader.get(WHERE).json()["notice"] == {"doing": "a workout"}


def test_a_freshly_composed_cora_holds_no_notice() -> None:
    """A notice lasts as long as the process does. Nothing is written down, so a cora
    started again is a cora that heard nothing yet."""
    app = _fields(FIELD)
    TestClient(api(app)).put(WHERE, json={"doing": "a workout"})

    assert TestClient(api(app)).get(WHERE).json()["notice"] is None


def test_the_notice_answers_the_two_methods_it_names_and_no_others() -> None:
    reader = _reader()

    assert reader.post(WHERE, json={"doing": "a workout"}).status_code == 405
    assert reader.delete(WHERE).status_code == 405


def test_a_notice_is_answered_as_json_whatever_it_holds() -> None:
    reader = _reader()

    reader.put(WHERE, json={"doing": "a workout", "sets": [1, 2], "done": False})

    held = reader.get(WHERE)
    assert "json" in held.headers["content-type"]
    assert json.loads(held.text)["notice"]["sets"] == [1, 2]
