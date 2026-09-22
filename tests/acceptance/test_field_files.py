from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.adapters.directory_files import DirectoryFiles
from cora.domain.errors import UnsettledFieldError
from cora.engine import keeping
from cora.engine.scoping import running_in
from cora.frontends.react.api import api
from cora.ports.host import Extension, Host
from fakes import FakeConversations

VOCAB = "vocab"
FILES = f"/api/scopes/{VOCAB}/files"
LIST = "| Deutsch | English |\n| --- | --- |\n| Apfel | apple |\n"
NAME = "Grundwortschatz.md"


def _served(tmp_path: Path) -> tuple[TestClient, Host]:
    # A deployment offering one field, and the host that field's plugin was handed.
    held: dict[str, Host] = {}

    def extend(cora: Host) -> None:
        held["cora"] = cora
        cora.register_instructions("A field of words.", scope=VOCAB)

    app = assembled(
        plugins=(Extension(module=VOCAB, extend=extend),),
        files=DirectoryFiles.at(str(tmp_path)),
        conversations=FakeConversations(),
        scopes=(VOCAB,),
    )
    return TestClient(api(app)), held["cora"]


def test_what_the_screen_writes_the_fields_plugin_reads(tmp_path: Path) -> None:
    page, cora = _served(tmp_path)

    assert page.put(f"{FILES}/{NAME}", json={"text": LIST}).status_code == 200

    with keeping.bound({}), running_in(frozenset({VOCAB})):
        assert cora.files.read(NAME) == LIST
        assert cora.files.names() == (NAME,)


def test_a_field_lists_what_it_holds(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    page.put(f"{FILES}/b.md", json={"text": LIST})
    page.put(f"{FILES}/a.md", json={"text": LIST})

    assert page.get(FILES).json() == {"names": ["a.md", "b.md"]}


def test_a_field_that_keeps_nothing_lists_nothing(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.get(FILES).json() == {"names": []}


def test_a_file_is_read_back_by_name(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    page.put(f"{FILES}/{NAME}", json={"text": LIST})

    assert page.get(f"{FILES}/{NAME}").json() == {"name": NAME, "text": LIST}


def test_a_second_write_under_one_name_replaces_the_first(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    page.put(f"{FILES}/{NAME}", json={"text": LIST})

    page.put(f"{FILES}/{NAME}", json={"text": "later"})

    assert page.get(f"{FILES}/{NAME}").json()["text"] == "later"


def test_reading_a_name_nothing_was_written_under_says_so(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.get(f"{FILES}/nothing.md").status_code == 404


def test_a_file_is_deleted_and_stops_being_listed(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    page.put(f"{FILES}/{NAME}", json={"text": LIST})

    assert page.delete(f"{FILES}/{NAME}").status_code == 204

    assert page.get(FILES).json() == {"names": []}
    assert page.get(f"{FILES}/{NAME}").status_code == 404


def test_deleting_what_is_not_there_is_not_an_error(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.delete(f"{FILES}/never.md").status_code == 204


def test_a_name_that_would_leave_the_directory_is_refused(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    (tmp_path / "outside.md").write_text("secret")

    refused = page.put(f"{FILES}/%2e%2e%2foutside.md", json={"text": "pwned"})

    assert refused.status_code in (400, 404)
    assert (tmp_path / "outside.md").read_text() == "secret"


def test_a_name_that_is_not_one_plain_name_is_refused(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.put(f"{FILES}/.hidden", json={"text": "x"}).status_code == 400


def test_a_file_over_the_cap_is_refused(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    too_big = page.put(f"{FILES}/{NAME}", json={"text": "x" * 1_000_001})

    assert too_big.status_code in (400, 413)
    assert page.get(FILES).json() == {"names": []}


def test_a_write_that_is_not_a_file_is_refused(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.put(f"{FILES}/{NAME}", json={"nope": 1}).status_code == 400


def test_a_field_the_deployment_does_not_offer_is_refused(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)

    assert page.get("/api/scopes/nosuch/files").status_code == 400


# The whole point of the seam: a file is the field's own data, and the search index and
# the document rail never hear about it.
def test_a_file_is_not_a_document(tmp_path: Path) -> None:
    page, _ = _served(tmp_path)
    page.put(f"{FILES}/{NAME}", json={"text": LIST})

    assert page.get(f"/api/documents?scope={VOCAB}").json() == []


def test_a_turn_in_two_fields_is_refused_in_a_sentence_naming_them(
    tmp_path: Path,
) -> None:
    # The files are keyed by field and the turn is in two, so which one a name belongs
    # to is not settled. The way out is asking under one, which the sentence says.
    _, cora = _served(tmp_path)

    with (
        keeping.bound({}),
        running_in(frozenset({VOCAB, "notes"})),
        pytest.raises(UnsettledFieldError) as refused,
    ):
        cora.files.read(NAME)

    said = refused.value.user_message
    assert "notes" in said and VOCAB in said
    assert said.endswith("Ask under one field.")
