from typing import Any

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.frontends.react import server
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeMemory

TOKEN = "acceptance-only-token"


def test_network_startup_protects_data_and_allows_authenticated_mutations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in ("CORA_HOST", "CORA_PORT", "CORA_NETWORK", "CORA_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "unused-model-key")
    monkeypatch.setenv("CORA_HOST", "0.0.0.0")
    monkeypatch.setenv("CORA_PORT", "9000")
    monkeypatch.setenv("CORA_NETWORK", "1")
    monkeypatch.setenv("CORA_API_TOKEN", TOKEN)
    memory = FakeMemory(("A private fact.",))
    app = assembled(memory=memory)
    monkeypatch.setattr(server, "live", lambda config: app)

    def run(served: Any, *, host: str, port: int) -> None:
        assert (host, port) == ("0.0.0.0", 9000)
        with TestClient(served) as reader:
            assert reader.get("/api/memory").status_code == 401
            assert reader.delete("/api/memory").status_code == 401
            assert [fact.text for fact in memory.recall()] == ["A private fact."]
            assert reader.get("/api/memory", auth=("cora", TOKEN)).json() == [
                {"key": "f1", "text": "A private fact."}
            ]
            where = f"/api/scopes/{DEFAULT_SCOPE}/notice"
            assert reader.put(where, json={"ready": True}).status_code == 401
            assert (
                reader.put(
                    where, json={"ready": True}, auth=("cora", TOKEN)
                ).status_code
                == 200
            )
            assert reader.get(where, auth=("cora", TOKEN)).json()["notice"] == {
                "ready": True
            }
            assert reader.delete("/api/memory", auth=("cora", TOKEN)).status_code == 204
            assert memory.recall() == ()

    monkeypatch.setattr(server.uvicorn, "run", run)
    server.serve()
