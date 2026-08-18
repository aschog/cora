import pathlib

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
