import pytest

from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME, itinerary_tool
from cora.ports.plugin import ToolRefusal
from fakes import FakeOutput

TITLE = "Kyoto, three days"
PLAN = "Day 1 — Fushimi Inari at dawn.\nDay 2 — Arashiyama."


def test_the_tool_writes_the_itinerary_and_answers_with_where_it_is() -> None:
    """What the user keeps is a file they can open, and the turn has to be able to say
    where it went — an effect nobody can find is an effect that may as well not have
    happened. The title becomes the filename, because a plan is looked for by name."""
    output = FakeOutput()
    tool = itinerary_tool(output)

    said = tool.run(title=TITLE, itinerary=PLAN)

    [(name, kept)] = output.written.items()
    assert kept == f"# {TITLE}\n\n{PLAN}\n"
    assert name.startswith("kyoto-three-days-") and name.endswith(".md")
    assert f"/kept/{name}" in said


def test_the_tool_declares_that_it_changes_something_outside_cora() -> None:
    """The declaration is the whole reason the gate stops for it, and it is the tool's
    own to make: only the tool knows a call of it writes."""
    tool = itinerary_tool(FakeOutput())

    assert tool.name == ITINERARY_TOOL_NAME
    assert tool.effect
    assert not tool.untrusted, "what it answers is cora's own words, not a service's"


def test_a_title_that_leaves_no_filename_is_refused_not_renamed() -> None:
    """The title is the model's prose, so turning it into a name is the plugin's job.
    Nothing left of it is a refusal rather than an invented name: a file the user cannot
    recognise, among the ones they approved, is worse than a call that failed."""
    output = FakeOutput()
    tool = itinerary_tool(output)

    with pytest.raises(ToolRefusal):
        tool.run(title="...", itinerary=PLAN)

    assert output.written == {}


def test_two_itineraries_under_one_title_are_two_files() -> None:
    """A revised plan saved under the same title must not take the earlier one with it.
    This is a file the user approved and keeps, so it is the upload store's rule: the
    head of the content's hash is in the name, and one title saved twice is two files
    rather than one overwritten."""
    output = FakeOutput()
    tool = itinerary_tool(output)

    tool.run(title=TITLE, itinerary=PLAN)
    tool.run(title=TITLE, itinerary=f"{PLAN}\nDay 3 — Nishiki.")

    assert len(output.written) == 2
    assert all(name.startswith("kyoto-three-days-") for name in output.written)


def test_the_same_itinerary_saved_twice_is_one_file() -> None:
    """The name is made out of what was saved, so saving the identical plan again is the
    same file rather than a second copy of it."""
    output = FakeOutput()
    tool = itinerary_tool(output)

    tool.run(title=TITLE, itinerary=PLAN)
    tool.run(title=TITLE, itinerary=PLAN)

    assert len(output.written) == 1
