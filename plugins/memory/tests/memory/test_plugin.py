import logging

import pytest

from cora.domain.errors import MemoryStoreError
from cora.plugins.memory import extend
from cora.ports.host import BRIEFING, HANDLER, INSTRUCTIONS, TOOL
from fakes import FailingMemory, FakeMemory, host_for


def test_with_a_memory_it_registers_remember_a_section_and_a_briefing_handler() -> None:
    host = host_for("cora.plugins.memory", memory=FakeMemory())

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (TOOL, None),
        (INSTRUCTIONS, None),
        (HANDLER, None),
    ]
    tool, section, handler = (entry.value for entry in host.registered)
    assert tool.name == "remember"
    assert "remember" in section
    assert handler.event == BRIEFING


def test_without_a_memory_it_registers_nothing_and_says_why(
    caplog: pytest.LogCaptureFixture,
) -> None:
    host = host_for("cora.plugins.memory")

    with caplog.at_level(logging.INFO, logger="cora.plugin.memory"):
        extend(host)

    assert host.registered == []
    assert any("no memory" in record.getMessage() for record in caplog.records)


def test_a_store_that_cannot_be_read_makes_the_handler_raise() -> None:
    host = host_for("cora.plugins.memory", memory=FailingMemory(MemoryStoreError()))
    extend(host)
    [handler] = [entry.value for entry in host.registered if entry.kind == HANDLER]

    with pytest.raises(MemoryStoreError):
        handler.handle("SYS")
