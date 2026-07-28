import socket
from pathlib import Path

import pytest

from app_server import app_env, find_free_port, running_app
from stub_llm import StubLlm


def test_the_launched_app_inherits_none_of_the_developers_knobs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CORA_HISTORY_TURNS", "0")
    monkeypatch.setenv("CORA_PLUGIN", "some.other.plugin")

    env = app_env(
        base_url="http://127.0.0.1:1/v1",
        api_key="dummy-key",
        db_path=tmp_path,
        model="stub-model",
    )

    assert "CORA_HISTORY_TURNS" not in env
    assert "CORA_PLUGIN" not in env
    assert env["CORA_DB_PATH"] == str(tmp_path)


def test_find_free_port_returns_a_port_the_caller_can_bind() -> None:
    port = find_free_port()

    with socket.socket() as claimed:
        claimed.bind(("127.0.0.1", port))

    assert 1024 < port < 65536


@pytest.mark.integration
def test_the_launched_app_serves_health_then_stops_on_teardown(tmp_path: Path) -> None:
    with (
        StubLlm() as stub,
        running_app(
            base_url=stub.base_url, api_key="dummy-key", db_path=tmp_path
        ) as server,
    ):
        assert server.health() == "ok"
        assert server.is_running

    assert not server.is_running
