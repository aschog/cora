import socket
from pathlib import Path

import pytest

from app_server import find_free_port, running_app
from stub_llm import StubLlm


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
