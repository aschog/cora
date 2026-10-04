import base64
import hashlib
import pathlib

import pytest
from starlette.testclient import TestClient

from app_builder import assembled, indexed
from cora.app.assembly import App
from cora.frontends.react.api import api
from cora.ports.host import DEFAULT_SCOPE, Extension, Host
from fakes import FakeMemory

TOKEN = "test-only-operator-token"
FIELD = "training"
NOTICE = f"/api/scopes/{FIELD}/notice"
PRIVATE = b"Private uploaded notes."


@pytest.mark.parametrize(
    "authorization",
    [
        "Basic",
        "Basic !not-base64!",
        "Basic " + base64.b64encode(b"cora").decode(),
        "Basic " + base64.b64encode(b"somebody:" + TOKEN.encode()).decode(),
        "Basic " + base64.b64encode(b"cora:incorrect").decode(),
        "Basic " + base64.b64encode(b"cora:\xff").decode(),
        "Bearer " + TOKEN,
        "Digest " + TOKEN,
    ],
)
def test_bad_authentication_is_uniform_and_changes_no_state(authorization: str) -> None:
    memory = FakeMemory(("A private fact.",))
    with TestClient(api(assembled(memory=memory), token=TOKEN)) as reader:
        for method in ("GET", "DELETE"):
            refused = reader.request(
                method, "/api/memory", headers={"Authorization": authorization}
            )
            assert refused.status_code == 401
            assert refused.json() == {"error": "Authentication required."}
            assert refused.headers["www-authenticate"] == 'Basic realm="cora"'
            assert TOKEN not in refused.text
    assert [fact.text for fact in memory.recall()] == ["A private fact."]


@pytest.mark.parametrize("token", [TOKEN, "utf8-café:with-a-colon"])
def test_basic_api_clients_can_read_and_change_state(token: str) -> None:
    memory = FakeMemory(("A private fact.",))
    app = assembled(memory=memory)
    with TestClient(api(app, token=token)) as reader:
        reader.auth = ("cora", token)
        assert reader.get("/api/memory").json() == [
            {"key": "f1", "text": "A private fact."}
        ]
        uploaded = reader.post(
            "/api/documents", files={"file": ("notes.md", PRIVATE, "text/markdown")}
        )
        assert uploaded.status_code == 200
        assert app.knowledge_base.list_sources() == ["notes.md"]
        assert reader.delete("/api/memory").status_code == 204
        assert memory.recall() == ()
        where = f"/api/scopes/{DEFAULT_SCOPE}/notice"
        assert reader.put(where, json={"ready": True}).status_code == 200
        assert reader.get(where).json()["notice"] == {"ready": True}


def _surface(root: pathlib.Path) -> tuple[App, pathlib.Path]:
    page = root / "page"
    page.mkdir()
    (page / "index.html").write_text("<title>Private trainer</title>")
    (page / "app.js").write_text("const privateTraining = true")
    ui = root / "ui"
    ui.mkdir()
    (ui / "index.html").write_text("<title>Private cora</title>")
    (ui / "app.js").write_text("const privateCora = true")

    def extend(host: Host) -> None:
        host.register_instructions("You coach lifting.", scope=FIELD)
        host.register_page(page, scope=FIELD)

    app = indexed(
        assembled(
            plugins=(Extension(module="fixture_plugins.trainer", extend=extend),),
            memory=FakeMemory(("A private fact.",)),
        ),
        ("private.md", PRIVATE),
    )
    assert app.files is not None
    app.files.write(DEFAULT_SCOPE, "field.txt", b"Private field file.")
    return app, ui


def test_missing_credentials_protect_data_assets_and_mutations(
    tmp_path: pathlib.Path,
) -> None:
    app, ui = _surface(tmp_path)
    upload = hashlib.sha256(PRIVATE).hexdigest()
    with TestClient(api(app, ui=ui, token=TOKEN)) as reader:
        for method, path in (
            ("GET", "/api/memory"),
            ("DELETE", "/api/memory"),
            ("GET", "/api/documents"),
            ("POST", "/api/documents"),
            ("DELETE", f"/api/documents/{DEFAULT_SCOPE}/private.md"),
            ("GET", f"/api/uploads/{DEFAULT_SCOPE}/{upload}"),
            ("GET", f"/api/scopes/{DEFAULT_SCOPE}/files/field.txt"),
            ("PUT", f"/api/scopes/{DEFAULT_SCOPE}/files/field.txt"),
            ("GET", NOTICE),
            ("PUT", NOTICE),
            ("POST", "/api/ask"),
            ("POST", "/api/resume"),
            ("DELETE", "/api/plugins/trainer"),
            ("GET", f"/pages/{FIELD}/"),
            ("GET", f"/pages/{FIELD}/app.js"),
            ("GET", "/"),
            ("HEAD", "/"),
            ("GET", "/app.js"),
            ("GET", "/not-a-route"),
        ):
            response = reader.request(method, path)
            assert response.status_code == 401, (method, path)
            assert response.headers["www-authenticate"] == 'Basic realm="cora"'
            assert "Private" not in response.text
            assert TOKEN not in response.text
    assert app.memory is not None
    assert [fact.text for fact in app.memory.recall()] == ["A private fact."]
    assert app.knowledge_base.list_sources() == ["private.md"]
    assert app.files is not None
    assert app.files.read_bytes(DEFAULT_SCOPE, "field.txt") == b"Private field file."
