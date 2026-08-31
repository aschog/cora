from cora.app.listing import NOTHING, SYSTEM_WIDE, rendered
from cora.ports.host import HANDLER, INSTRUCTIONS, TOOL, Contributed, Listed

FITNESS = Listed(
    name="fitness",
    source="cora.plugins.fitness",
    contributions=(
        Contributed(INSTRUCTIONS, "", "fitness"),
        Contributed(TOOL, "bmr", "fitness"),
        Contributed(HANDLER, "screen"),
    ),
)


def test_the_rendering_names_every_plugin_and_marks_what_is_system_wide() -> None:
    printed = rendered((FITNESS, Listed(name="notes", source="/tmp/notes.py")))

    assert "fitness — cora.plugins.fitness" in printed
    assert "notes — /tmp/notes.py" in printed
    assert "bmr" in printed
    assert printed.count(SYSTEM_WIDE) == 1
    assert "registers nothing" in printed


def test_a_bare_cora_says_so_rather_than_printing_a_blank() -> None:
    assert rendered(()) == NOTHING
