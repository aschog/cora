from cora.plugins.documents import DEFAULT_TOP_K, RULE, extend
from cora.plugins.documents.search import SEARCH_TOOL_NAME, DocumentSearch
from cora.ports.host import HANDLER, INSTRUCTIONS, TOOL, UPLOADING
from fakes import host_for


def _registered(settings: dict[str, str] | None = None) -> list:
    host = host_for("cora.plugins.documents", settings=settings)
    extend(host)
    return host.registered


def test_it_registers_the_search_a_section_and_the_upload_handler_system_wide() -> None:
    registered = _registered()

    assert [(entry.kind, entry.scope) for entry in registered] == [
        (TOOL, None),
        (INSTRUCTIONS, None),
        (HANDLER, None),
    ]
    tool, section, handler = (entry.value for entry in registered)
    assert tool.name == SEARCH_TOOL_NAME
    assert section == RULE
    assert handler.event == UPLOADING


def test_the_depth_is_read_from_its_settings_and_defaults_to_five() -> None:
    [set_to] = [e.value for e in _registered({"top_k": "3"}) if e.kind == TOOL]
    [defaulted] = [e.value for e in _registered({"top_k": "lots"}) if e.kind == TOOL]

    assert isinstance(set_to.run, DocumentSearch) and set_to.run.top_k == 3
    assert isinstance(defaulted.run, DocumentSearch)
    assert defaulted.run.top_k == DEFAULT_TOP_K == 5


def test_the_section_names_the_search_the_citing_form_and_the_empty_search() -> None:
    assert SEARCH_TOOL_NAME in RULE
    assert "[n]" in RULE
    assert "uploaded nothing" in RULE
