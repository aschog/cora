"""A field's page, as the shell reaches it: served from the directory a plugin
registered, refused everywhere that directory does not reach, and live with the plugin.
"""

import pathlib
from typing import Any

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App, LiveApp
from cora.frontends.react.api import api
from cora.ports.host import Extension, Host

FIELD = "training"
ENTRY = "<!doctype html><title>Trainer</title>"
SCRIPT = "export const sets = 3\n"
WHERE = f"/pages/{FIELD}/"

DROPPED = """\
import pathlib

from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_page(pathlib.Path(__file__).parent / "page", scope="training")
"""


def _page(root: pathlib.Path) -> pathlib.Path:
    page = root / "page"
    page.mkdir(parents=True)
    (page / "index.html").write_text(ENTRY)
    (page / "app.js").write_text(SCRIPT)
    (root / "secret.txt").write_text("not under the page")
    return page


def _serving(page: pathlib.Path | None, **overrides: Any) -> App:
    def extend(cora: Host) -> None:
        cora.register_instructions("You coach lifting.", scope=FIELD)
        if page is not None:
            cora.register_page(page, scope=FIELD)

    return assembled(
        plugins=(Extension(module="fixture_plugins.trainer", extend=extend),),
        **overrides,
    )


def _dropped(folder: pathlib.Path) -> pathlib.Path:
    trainer = folder / "trainer"
    _page(trainer)
    (trainer / "__init__.py").write_text(DROPPED)
    return trainer


def test_the_path_a_field_reports_answers_its_entry_page(
    tmp_path: pathlib.Path,
) -> None:
    with TestClient(api(_serving(_page(tmp_path)))) as reader:
        served = reader.get(WHERE)

    assert served.status_code == 200
    assert served.text == ENTRY


def test_a_file_beside_the_entry_page_is_answered_as_what_it_is(
    tmp_path: pathlib.Path,
) -> None:
    with TestClient(api(_serving(_page(tmp_path)))) as reader:
        served = reader.get(f"{WHERE}app.js")

    assert served.status_code == 200
    assert served.text == SCRIPT
    assert "javascript" in served.headers["content-type"]


def test_a_request_spelling_its_way_above_the_directory_reaches_no_file(
    tmp_path: pathlib.Path,
) -> None:
    """The climb-out loop `/api/plugins/{name}` is already held to: a path a client
    wrote is never a path cora opens."""
    _page(tmp_path)

    with TestClient(api(_serving(tmp_path / "page"))) as reader:
        for spelling in (
            "../secret.txt",
            "..%2Fsecret.txt",
            "%2e%2e/secret.txt",
            "/etc/hosts",
            "page/../../secret.txt",
        ):
            climbed = reader.get(f"{WHERE}{spelling}")

            assert climbed.status_code == 404, spelling
            assert "not under the page" not in climbed.text


def test_the_path_of_a_field_whose_plugin_brought_no_page_is_refused() -> None:
    with TestClient(api(_serving(None))) as reader:
        assert reader.get(WHERE).status_code == 404


def test_the_path_of_a_field_nothing_loaded_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    with TestClient(api(_serving(_page(tmp_path)))) as reader:
        assert reader.get("/pages/travel/").status_code == 404


def test_a_page_whose_directory_went_away_is_refused_rather_than_raising(
    tmp_path: pathlib.Path,
) -> None:
    """Registering is not held against the disk, so this is the case that check would
    have bought — and it costs one path a refusal rather than every request."""
    page = _page(tmp_path)
    app = _serving(page)
    (page / "index.html").unlink()
    (page / "app.js").unlink()
    page.rmdir()

    with TestClient(api(app)) as reader:
        assert reader.get(WHERE).status_code == 404


def test_a_page_reached_through_a_symlink_is_served(
    tmp_path: pathlib.Path,
) -> None:
    """How this repository's own plugins are deployed: the folder holds a link, and
    what it points at is somewhere else entirely."""
    elsewhere = tmp_path / "elsewhere"
    _page(elsewhere)
    linked = tmp_path / "linked"
    linked.symlink_to(elsewhere / "page", target_is_directory=True)

    with TestClient(api(_serving(linked))) as reader:
        assert reader.get(WHERE).text == ENTRY


def test_a_symlink_inside_the_directory_is_not_followed_out_of_it(
    tmp_path: pathlib.Path,
) -> None:
    """What the contract promises a plugin author, so the promise is held here rather
    than by the static server's own default staying what it is."""
    page = _page(tmp_path)
    (page / "leak.txt").symlink_to(tmp_path / "secret.txt")

    with TestClient(api(_serving(page))) as reader:
        leaked = reader.get(f"{WHERE}leak.txt")

    assert leaked.status_code == 404
    assert "not under the page" not in leaked.text


def test_coras_own_page_still_answers_at_the_root(tmp_path: pathlib.Path) -> None:
    """The shell is mounted at the root and matches everything, so a page route stands
    before it — and has to leave what it was standing before alone."""
    shell = tmp_path / "dist"
    shell.mkdir()
    (shell / "index.html").write_text("<!doctype html><title>cora</title>")

    with TestClient(api(_serving(_page(tmp_path)), ui=shell)) as reader:
        assert "cora" in reader.get("/").text
        assert reader.get(WHERE).text == ENTRY


def test_an_edited_page_file_is_answered_as_it_now_stands(
    tmp_path: pathlib.Path,
) -> None:
    page = _page(tmp_path)

    with TestClient(api(_serving(page))) as reader:
        assert reader.get(WHERE).text == ENTRY
        (page / "index.html").write_text("<!doctype html><title>Two</title>")

        assert reader.get(WHERE).text == "<!doctype html><title>Two</title>"


def test_a_served_file_asks_to_be_revalidated_before_it_is_reused(
    tmp_path: pathlib.Path,
) -> None:
    """Without this the live folder is a lie one cache deep: a response carrying only a
    modification time may be reused without asking."""
    with TestClient(api(_serving(_page(tmp_path)))) as reader:
        assert reader.get(WHERE).headers["cache-control"] == "no-cache"
        assert reader.get(f"{WHERE}app.js").headers["cache-control"] == "no-cache"


def test_a_plugin_dropped_into_the_folder_has_its_page_served(
    tmp_path: pathlib.Path,
) -> None:
    holder = LiveApp(
        named=(), folder=tmp_path, compose=lambda loaded: assembled(plugins=loaded)
    )
    reader = TestClient(api(holder))
    assert reader.get(WHERE).status_code == 404

    _dropped(tmp_path)

    assert reader.get(WHERE).text == ENTRY


def test_the_page_of_a_plugin_taken_out_of_the_folder_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    trainer = _dropped(tmp_path)
    holder = LiveApp(
        named=(), folder=tmp_path, compose=lambda loaded: assembled(plugins=loaded)
    )
    reader = TestClient(api(holder))
    assert reader.get(WHERE).text == ENTRY

    (trainer / "__init__.py").unlink()

    assert reader.get(WHERE).status_code == 404


def test_a_field_whose_name_a_url_would_read_as_syntax_is_still_reachable(
    tmp_path: pathlib.Path,
) -> None:
    """Nothing holds a field name to what a URL finds unremarkable, and the address
    reported for a page is the one that has to answer."""
    odd = "strength & conditioning#2"

    def extend(cora: Host) -> None:
        cora.register_page(_page(tmp_path), scope=odd)

    app = assembled(plugins=(Extension(module="fixture_plugins.odd", extend=extend),))

    with TestClient(api(app)) as reader:
        where = reader.get("/api/scopes").json()["pages"][odd]

        assert reader.get(where).text == ENTRY
