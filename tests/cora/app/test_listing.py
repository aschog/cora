import pytest

from cora.app.listing import SYSTEM_WIDE, main, rendered
from cora.ports.host import (
    HANDLER,
    INSTRUCTIONS,
    PAGE,
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


def test_the_rendering_names_every_plugin_and_marks_what_is_system_wide() -> None:
    printed = rendered((FITNESS, Listed(name="notes", source="/tmp/notes.py")))

    assert "fitness — cora.plugins.fitness" in printed
    assert "notes — /tmp/notes.py" in printed
    assert "bmr" in printed
    assert printed.count(SYSTEM_WIDE) == 1
    assert "registers nothing" in printed


def test_a_deployment_that_cannot_be_assembled_says_so_in_one_sentence(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit) as stopped:
        main()

    assert stopped.value.code != 0
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
    assert stopped.value.__cause__ is None, "a traceback is not the answer"


def test_a_page_prints_under_its_field_on_a_line_of_its_own() -> None:
    printed = rendered(
        (
            Listed(
                name="coach",
                source="/tmp/coach",
                contributions=(Contributed(PAGE, "", "fitness"),),
            ),
        )
    )

    assert "page" in printed
    assert "fitness" in printed
    assert SYSTEM_WIDE not in printed
