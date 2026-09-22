import pathlib

import pytest

from cora.domain.errors import ConfigurationError
from cora.frontends.react import server


def test_the_build_is_looked_for_beside_the_package() -> None:
    assert server.DEFAULT_UI.parts[-2:] == ("ui", "dist")
    assert server.DEFAULT_UI.parent.is_dir(), (
        f"{server.DEFAULT_UI.parent} is not this repository's ui/ directory"
    )
    assert (server.DEFAULT_UI.parent / "package.json").is_file()


def test_the_deployment_can_say_where_the_build_is() -> None:
    assert server.ui_path({"CORA_UI_PATH": "/srv/cora/page"}) == pathlib.Path(
        "/srv/cora/page"
    )


@pytest.mark.parametrize("given", ["8O00", "eight thousand", "80.80"])
def test_a_port_that_is_not_a_number_says_so_rather_than_raising_a_traceback(
    given: str,
) -> None:
    with pytest.raises(ConfigurationError) as refused:
        server.port({"CORA_PORT": given})

    assert "CORA_PORT" in refused.value.user_message
    assert given in refused.value.user_message


def test_nothing_is_built_before_the_settings_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "not-used-because-the-port-fails-first")
    monkeypatch.setenv("CORA_PORT", "8O00")
    monkeypatch.setattr(
        server,
        "live",
        lambda config: pytest.fail("the app was assembled for a port cora cannot read"),
    )

    with pytest.raises(SystemExit):
        server.serve()
