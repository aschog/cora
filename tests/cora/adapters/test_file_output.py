import pathlib

import pytest

from cora.adapters.file_output import FileOutput
from cora.domain.errors import AdapterError
from cora.ports.plugin import ToolRefusal

ITINERARY = "Day 1 — Fushimi Inari at dawn."


def test_a_write_lands_under_the_root_and_says_where_it_landed(
    tmp_path: pathlib.Path,
) -> None:
    """The one thing a tool needs back: somewhere it can tell the user about. The root
    is made on the way, so a deployment that configured a location it never used is not
    a deployment that has to create a directory by hand."""
    output = FileOutput.at(str(tmp_path / "kept"))

    where = output.write("kyoto.md", ITINERARY)

    landed = pathlib.Path(where)
    assert landed.read_text() == ITINERARY
    assert landed.parent == tmp_path / "kept"


@pytest.mark.parametrize(
    "name", ["../escaped.md", "../../escaped.md", "/tmp/escaped.md", "", "   "]
)
def test_a_name_that_does_not_stay_under_the_root_is_refused(
    tmp_path: pathlib.Path, name: str
) -> None:
    """Confinement is the adapter's, so no plugin writes the check itself — and nothing
    is written outside the location, which is the whole claim."""
    root = tmp_path / "kept"
    output = FileOutput.at(str(root))

    with pytest.raises(ToolRefusal):
        output.write(name, ITINERARY)

    assert list(tmp_path.rglob("*.md")) == []


def test_a_root_that_cannot_be_written_fails_as_the_outside_world_failing(
    tmp_path: pathlib.Path,
) -> None:
    """A refusal is the plugin asking for something it may not have; this is the disk
    saying no, which is a different thing and reads as one."""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory")
    output = FileOutput.at(str(blocked))

    with pytest.raises(AdapterError):
        output.write("kyoto.md", ITINERARY)


@pytest.mark.parametrize("name", ["kyoto\x00.md", "ky\x00oto/plan.md"])
def test_a_name_that_is_not_a_path_at_all_is_refused_as_a_name(
    tmp_path: pathlib.Path, name: str
) -> None:
    """A NUL byte makes a string something no filesystem can resolve. It is refused as
    the bad name it is, rather than raising out of the resolution as a `ValueError` the
    port never said it could."""
    output = FileOutput.at(str(tmp_path))

    with pytest.raises(ToolRefusal):
        output.write(name, ITINERARY)
