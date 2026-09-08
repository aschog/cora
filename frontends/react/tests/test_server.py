import pathlib

import pytest

from cora.domain.errors import ConfigurationError
from cora.frontends.react import server


def test_the_build_is_looked_for_beside_the_package() -> None:
    """`ui/dist` is Vite's output, not a Python module, so it is found by walking out
    of the package rather than by being packaged. An off-by-one in that walk serves the
    API with no page and says nothing, so the walk is asserted against the tree."""
    assert server.DEFAULT_UI.parts[-2:] == ("ui", "dist")
    assert server.DEFAULT_UI.parent.is_dir(), (
        f"{server.DEFAULT_UI.parent} is not this repository's ui/ directory"
    )
    assert (server.DEFAULT_UI.parent / "package.json").is_file()


def test_the_deployment_can_say_where_the_build_is() -> None:
    """An installed wheel has no `ui/` beside it — `CORA_UI_PATH` is how that
    deployment names the build it serves."""
    assert server.ui_path({"CORA_UI_PATH": "/srv/cora/page"}) == pathlib.Path(
        "/srv/cora/page"
    )


@pytest.mark.parametrize("given", ["8O00", "eight thousand", "80.80"])
def test_a_port_that_is_not_a_number_says_so_rather_than_raising_a_traceback(
    given: str,
) -> None:
    """Every other numeric setting is parsed through one contract, which names the
    variable and quotes what it was given. A bare `int()` here dies with a `ValueError`
    out of uvicorn's arguments instead: a traceback where the app promises a
    sentence."""
    with pytest.raises(ConfigurationError) as refused:
        server.port({"CORA_PORT": given})

    assert "CORA_PORT" in refused.value.user_message
    assert given in refused.value.user_message


def test_nothing_is_built_before_the_settings_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mistyped port is a typo, and assembling the app for it is an embedding model
    the operator waits through before being told. The sentence, the exit code and the
    absent traceback all hold whichever order it happens in, so the order is what is
    asserted here: a `live` that fails the test if it is reached at all."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-because-the-port-fails-first")
    monkeypatch.setenv("CORA_PORT", "8O00")
    monkeypatch.setattr(
        server,
        "live",
        lambda config: pytest.fail("the app was assembled for a port cora cannot read"),
    )

    with pytest.raises(SystemExit):
        server.serve()
