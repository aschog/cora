import pytest

from cora.app.listing import NOTHING, SYSTEM_WIDE, main, rendered
from cora.ports.host import (
    HANDLER,
    HAS_AN_EFFECT,
    INSTRUCTIONS,
    TOOL,
    Contributed,
    Listed,
)

FITNESS = Listed(
    name="fitness",
    source="cora.plugins.fitness",
    contributions=(
        Contributed(INSTRUCTIONS, "", "fitness"),
        Contributed(TOOL, "bmr", "fitness"),
        Contributed(HANDLER, "screen"),
    ),
)
TRAVEL = Listed(
    name="travel",
    source="cora.plugins.travel",
    contributions=(
        Contributed(TOOL, "look_up", "travel"),
        Contributed(TOOL, "book_it", "travel", HAS_AN_EFFECT),
    ),
)


def test_a_registration_with_something_more_to_say_says_it_beside_itself() -> None:
    """What a plugin may do is what the listing is for, and a tool that changes
    something outside cora is the loudest thing it can say. Read off the note rather
    than off the kind, so the rendering shows one it has never heard of."""
    printed = rendered((TRAVEL,))

    [_, reading, acting] = printed.splitlines()
    assert HAS_AN_EFFECT in acting
    assert HAS_AN_EFFECT not in reading


def test_the_rendering_names_every_plugin_and_marks_what_is_system_wide() -> None:
    printed = rendered((FITNESS, Listed(name="notes", source="/tmp/notes.py")))

    assert "fitness — cora.plugins.fitness" in printed
    assert "notes — /tmp/notes.py" in printed
    assert "bmr" in printed
    assert printed.count(SYSTEM_WIDE) == 1
    assert "registers nothing" in printed


def test_a_bare_cora_says_so_rather_than_printing_a_blank() -> None:
    assert rendered(()) == NOTHING


def test_a_deployment_that_cannot_be_assembled_says_so_in_one_sentence(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The refusal was written to be read by whoever ran the command, and the traceback
    it arrives under buries the one line they can act on — the same reading the shell's
    own entry point takes."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit) as stopped:
        main()

    assert stopped.value.code != 0
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
    assert stopped.value.__cause__ is None, "a traceback is not the answer"
