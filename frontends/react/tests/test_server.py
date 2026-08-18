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


def test_a_blank_path_reads_as_unset_like_every_other_setting() -> None:
    assert server.ui_path({"CORA_UI_PATH": "  "}) == server.DEFAULT_UI
    assert server.ui_path({}) == server.DEFAULT_UI


def test_the_deployment_can_say_which_port_to_serve_on() -> None:
    assert server.port({"CORA_PORT": "9000"}) == 9000


def test_a_blank_port_reads_as_unset_like_every_other_setting() -> None:
    assert server.port({"CORA_PORT": "  "}) == server.DEFAULT_PORT
    assert server.port({}) == server.DEFAULT_PORT


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


@pytest.mark.parametrize("given", ["0", "-1"])
def test_a_port_no_server_can_bind_is_refused_rather_than_handed_on(given: str) -> None:
    with pytest.raises(ConfigurationError):
        server.port({"CORA_PORT": given})


def test_a_setting_the_process_cannot_use_reaches_the_operator_as_a_sentence(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ConfigurationError` carries a message written for whoever ran cora, and the
    whole app promises no failure arrives as a stack. `make run-react` with a mistyped
    port printed the traceback that message happened to be the last line of."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-because-the-port-fails-first")
    monkeypatch.setenv("CORA_PORT", "8O00")

    with pytest.raises(SystemExit) as stopped:
        server.serve()

    assert stopped.value.code != 0
    said = capsys.readouterr().err
    assert "CORA_PORT" in said and "8O00" in said
    assert "Traceback" not in said
