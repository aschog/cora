import pathlib

from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import LiveApp
from cora.frontends.react.api import api
from fakes import FakeDocuments, FakeRetriever

DROPPED = """\
from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


def _reader(folder: pathlib.Path) -> TestClient:
    retriever, documents = FakeRetriever(), FakeDocuments()
    return TestClient(
        api(
            LiveApp(
                named=(),
                folder=folder,
                compose=lambda loaded: assembled(
                    plugins=loaded,
                    retriever=retriever,
                    documents=documents,
                    plugins_folder=folder,
                ),
            )
        )
    )


def test_deleting_a_plugin_answers_no_content_and_takes_its_entry(
    tmp_path: pathlib.Path,
) -> None:
    dropped = tmp_path / "field_notes.py"
    dropped.write_text(DROPPED)
    reader = _reader(tmp_path)

    gone = reader.delete("/api/plugins/field_notes")

    assert gone.status_code == 204 and not gone.content
    assert not dropped.exists()


def test_the_listing_and_the_fields_drop_it_on_the_next_read(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "field_notes.py").write_text(DROPPED)
    reader = _reader(tmp_path)
    assert [each["name"] for each in reader.get("/api/plugins").json()] == [
        "field_notes"
    ]

    reader.delete("/api/plugins/field_notes")

    assert reader.get("/api/plugins").json() == []
    assert reader.get("/api/scopes").json()["available"] == []


def test_a_delete_that_is_refused_says_why(tmp_path: pathlib.Path) -> None:
    (tmp_path / "field_notes.py").write_text(DROPPED)
    reader = _reader(tmp_path)

    refused = reader.delete("/api/plugins/voyage")

    assert refused.status_code == 400
    assert "voyage" in refused.json()["error"]
    assert (tmp_path / "field_notes.py").exists()


def test_a_name_that_is_a_path_reaches_no_file(tmp_path: pathlib.Path) -> None:
    """The route takes one path segment, and the name it takes is matched against what
    loaded — so a traversal is a 404 or a refusal, never a file."""
    (tmp_path / "field_notes.py").write_text(DROPPED)
    reader = _reader(tmp_path)

    for named in ("..%2Ffield_notes", "field_notes.py", "%2Fetc%2Fhosts"):
        assert reader.delete(f"/api/plugins/{named}").status_code in (400, 404)

    assert (tmp_path / "field_notes.py").exists()


def test_the_listing_says_which_plugins_can_be_deleted(
    tmp_path: pathlib.Path,
) -> None:
    """Cora's answer rather than the page's reading of a source: a module named in the
    environment is fixed at start, and the page has no control to offer for it."""
    (tmp_path / "field_notes.py").write_text(DROPPED)
    reader = _reader(tmp_path)

    assert [
        (each["name"], each["deletable"]) for each in reader.get("/api/plugins").json()
    ] == [("field_notes", True)]
