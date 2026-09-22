import pathlib

from app_builder import assembled
from cora.engine.plugin_registry import load_plugins
from cora.ports.host import (
    BRIEFING,
    CALLING,
    HANDLER,
    INSTRUCTIONS,
    RETURNING,
    TOOL,
)

NAMED = "fixture_plugins.taking_part"
DROPPED = """\
from cora.ports.host import Host

SCOPE = "birds"

def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope=SCOPE)
    cora.register_tool(
        name="count_species",
        description="How many species were seen on a given day.",
        parameter_schema={"type": "object", "properties": {}},
        run=lambda: 3,
        scope=SCOPE,
    )
"""


def test_a_named_module_and_a_dropped_file_are_both_loaded_and_both_listed(
    tmp_path: pathlib.Path,
) -> None:
    folder = tmp_path / "plugins"
    folder.mkdir()
    dropped = folder / "field_notes.py"
    dropped.write_text(DROPPED)

    app = assembled(plugins=load_plugins([NAMED], folder=folder), scopes=("birds",))

    listed = {each.name: each for each in app.plugins}
    assert sorted(listed) == ["field_notes", "taking_part"]

    installed = listed["taking_part"]
    assert installed.source == NAMED
    assert [each.name for each in installed.of(TOOL)] == ["shipping", "lookup"]
    assert [each.name for each in installed.of(HANDLER)] == [
        BRIEFING,
        CALLING,
        RETURNING,
    ]
    assert all(each.system_wide for each in installed.contributions)

    read = listed["field_notes"]
    assert read.source == str(dropped)
    assert read.scopes == ("birds",)
    assert [each.name for each in read.of(TOOL)] == ["count_species"]
    assert read.of(INSTRUCTIONS)
    assert not any(each.system_wide for each in read.contributions)
