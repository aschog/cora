import pytest

from cora.domain.errors import PluginLoadError
from cora.plugins.interview import SCOPE, STYLE, extend
from cora.plugins.interview.prompts import STYLES
from cora.plugins.interview.tools import REPORT_TOOL_NAME
from cora.ports.host import HANDLER, SCREENING, TOOL
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import FakeOutput, host_for


def test_everything_is_scoped_and_only_the_save_has_an_effect() -> None:
    """Nothing here is system-wide — the misuse screen included, because cora's
    security plugin holds that line — and the one effect is the file the user keeps."""
    host = host_for("cora.plugins.interview", output=FakeOutput())

    extend(host)

    under = [(entry.kind, entry.scope) for entry in host.registered]
    assert under.count((TOOL, SCOPE)) == 3
    assert under.count((SAYS, SCOPE)) == 1
    assert under.count((HANDLER, SCOPE)) == 1
    assert len(under) == 5
    [screen] = [entry for entry in host.registered if entry.kind == HANDLER]
    assert screen.value.event == SCREENING
    effects = [
        entry.value
        for entry in host.registered
        if entry.kind == TOOL and entry.value.effect
    ]
    assert [tool.name for tool in effects] == [REPORT_TOOL_NAME]


def test_without_somewhere_to_write_the_save_is_never_offered() -> None:
    """A tool the model can call and that can only fail is worse than one it was
    never offered."""
    host = host_for("cora.plugins.interview")

    extend(host)

    tools = [entry.value for entry in host.registered if entry.kind == TOOL]
    assert len(tools) == 2
    assert not any(tool.effect for tool in tools)


def test_the_style_setting_picks_which_instructions_register() -> None:
    host = host_for("cora.plugins.interview", settings={STYLE: "chain_of_thought"})

    extend(host)

    [instructions] = [entry.value for entry in host.registered if entry.kind == SAYS]
    assert instructions == STYLES["chain_of_thought"]


def test_a_style_nobody_wrote_is_refused_at_load_by_name() -> None:
    """The refusal names the setting and the stray value, so the deployment is told
    what to fix rather than a typo quietly becoming the default."""
    host = host_for("cora.plugins.interview", settings={STYLE: "vibes"})

    with pytest.raises(PluginLoadError) as refused:
        extend(host)

    assert STYLE in str(refused.value)
    assert "vibes" in str(refused.value)


def test_every_style_opens_with_the_same_line_for_the_router() -> None:
    """The first line is what routes an unpinned turn here, so routing must not
    depend on which style the deployment picked."""
    first_lines = {text.split("\n", 1)[0] for text in STYLES.values()}

    assert len(first_lines) == 1
    assert "interview" in first_lines.pop().lower()


def test_the_five_styles_are_five_different_bodies() -> None:
    assert len(STYLES) == 5
    assert len(set(STYLES.values())) == 5
