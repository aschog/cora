import pathlib
from typing import Any

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.domain.errors import ConfigurationError
from cora.frontends.react import server


def test_default_startup_serves_loopback_without_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chosen = server.settings({})
    assert (chosen.host, chosen.port, chosen.token) == ("127.0.0.1", 8000, None)
    for key in ("CORA_HOST", "CORA_PORT", "CORA_NETWORK", "CORA_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused-model-key")
    monkeypatch.setattr(server, "live", lambda config: assembled())

    def run(served: Any, *, host: str, port: int) -> None:
        assert (host, port) == (chosen.host, chosen.port)
        with TestClient(served) as reader:
            assert reader.get("/api/scopes").status_code == 200

    monkeypatch.setattr(server.uvicorn, "run", run)
    server.serve()


@pytest.mark.parametrize("host", ["127.0.0.1", "127.23.45.67", "::1", "localhost"])
def test_explicit_loopback_bindings_need_no_token(host: str) -> None:
    chosen = server.settings({"CORA_HOST": host, "CORA_NETWORK": "0"})

    assert chosen.host == host
    assert chosen.token is None


def test_the_build_is_looked_for_beside_the_package() -> None:
    assert server.DEFAULT_UI.parts[-2:] == ("ui", "dist")
    assert server.DEFAULT_UI.parent.is_dir(), (
        f"{server.DEFAULT_UI.parent} is not this repository's ui/ directory"
    )
    assert (server.DEFAULT_UI.parent / "package.json").is_file()


def test_the_deployment_can_say_where_the_build_is() -> None:
    assert server.ui_path({"CORA_UI_PATH": "/srv/cora/page"}) == pathlib.Path(
        "/srv/cora/page"
    )


@pytest.mark.parametrize("given", ["8O00", "eight thousand", "80.80"])
def test_a_port_that_is_not_a_number_says_so_rather_than_raising_a_traceback(
    given: str,
) -> None:
    with pytest.raises(ConfigurationError) as refused:
        server.port({"CORA_PORT": given})

    assert "CORA_PORT" in refused.value.user_message
    assert given in refused.value.user_message


def test_nothing_is_built_before_the_settings_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-because-the-port-fails-first")
    monkeypatch.setenv("CORA_PORT", "8O00")
    monkeypatch.setattr(
        server,
        "live",
        lambda config: pytest.fail("the app was assembled for a port cora cannot read"),
    )

    with pytest.raises(SystemExit):
        server.serve()
