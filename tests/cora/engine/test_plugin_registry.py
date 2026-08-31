import pathlib
import sys

import pytest

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.engine.plugin_registry import load_plugin, load_plugins
from cora.ports.host import CONTRACT


def test_loading_a_plugin_hands_back_the_module_and_its_extend() -> None:
    """Loading imports and checks the module. What the plugin contributes is registered
    later, against a host, because a host is made of an assembled app's own parts."""
    loaded = load_plugin("fixture_plugins.valid")

    assert loaded.module == "fixture_plugins.valid"
    assert callable(loaded.extend)


def test_missing_plugin_module_raises_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.no_such_module")

    assert "fixture_plugins.no_such_module" in excinfo.value.user_message
    assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)


def test_plugin_with_missing_dependency_is_reported_as_failed_import() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.missing_dependency")

    assert "failed to import" in excinfo.value.user_message
    assert "was not found" not in excinfo.value.user_message


def test_plugin_module_raising_during_import_surfaces_as_typed_error() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin("fixture_plugins.broken_import")

    assert "fixture_plugins.broken_import" in excinfo.value.user_message
    assert isinstance(excinfo.value.__cause__, RuntimeError)


NOT_A_PLUGIN = [
    ("no_extend", "defines no extend"),
    ("wrong_type", "extend is not callable"),
]


@pytest.mark.parametrize(("fixture", "reason"), NOT_A_PLUGIN)
def test_a_module_that_is_not_a_plugin_is_refused_by_name(
    fixture: str, reason: str
) -> None:
    module_path = f"fixture_plugins.{fixture}"

    with pytest.raises(PluginLoadError) as excinfo:
        load_plugin(module_path)

    assert module_path in excinfo.value.user_message
    assert reason in excinfo.value.user_message


def test_one_bad_module_in_a_list_names_that_module_not_the_list() -> None:
    with pytest.raises(PluginLoadError) as excinfo:
        load_plugins(
            [
                "fixture_plugins.valid",
                "fixture_plugins.no_such_module",
                "fixture_plugins.rules_only",
            ]
        )

    assert "fixture_plugins.no_such_module" in excinfo.value.user_message
    assert "fixture_plugins.valid" not in excinfo.value.user_message


def test_one_module_named_twice_is_a_config_error() -> None:
    """Otherwise a tool-name collision reads as a plugin colliding with itself, and the
    user is told nothing about what they actually typed."""
    with pytest.raises(ConfigurationError) as excinfo:
        load_plugins(["fixture_plugins.valid", "fixture_plugins.valid"])

    assert "fixture_plugins.valid" in excinfo.value.user_message
    assert "twice" in excinfo.value.user_message


def test_two_modules_named_alike_at_the_end_are_refused() -> None:
    """A name is what tells two plugins apart: it heads their sections of the brief and
    it names their settings. Two `fitness` plugins would share both."""
    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["acme.plugins.valid", "fixture_plugins.valid"])

    assert "acme.plugins.valid" in refused.value.user_message
    assert "fixture_plugins.valid" in refused.value.user_message
    assert "Rename one" in refused.value.user_message


DROPPED = """\
from cora.ports.host import Host

def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


def _drop(folder: pathlib.Path, name: str, source: str = DROPPED) -> pathlib.Path:
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_text(source)
    return path


def test_a_named_module_is_its_own_source() -> None:
    assert load_plugin("fixture_plugins.valid").source == "fixture_plugins.valid"


def test_a_file_dropped_in_the_folder_is_loaded_under_its_stem(
    tmp_path: pathlib.Path,
) -> None:
    """No packaging at all: a `.py` file in the folder is a plugin, named for the file
    and sourced from where it lies."""
    dropped = _drop(tmp_path, "field_notes.py")

    loaded = load_plugins([], folder=tmp_path)

    assert [(each.module, each.source) for each in loaded] == [
        ("field_notes", str(dropped))
    ]


def test_the_folder_is_read_in_name_order_after_the_modules_named(
    tmp_path: pathlib.Path,
) -> None:
    """Load order is the only precedence there is, so it is one a deployment can
    predict rather than one the filesystem decides."""
    _drop(tmp_path, "zebra.py")
    _drop(tmp_path, "aardvark.py")

    loaded = load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert [each.module for each in loaded] == [
        "fixture_plugins.valid",
        "aardvark",
        "zebra",
    ]


def test_a_folder_that_is_not_there_holds_no_plugins(tmp_path: pathlib.Path) -> None:
    assert load_plugins([], folder=tmp_path / "nowhere") == ()


def test_a_dropped_file_that_fails_to_import_is_refused_by_its_filename(
    tmp_path: pathlib.Path,
) -> None:
    dropped = _drop(tmp_path, "broken.py", "raise RuntimeError('boom')\n")

    with pytest.raises(PluginLoadError) as refused:
        load_plugins([], folder=tmp_path)

    assert str(dropped) in refused.value.user_message
    assert isinstance(refused.value.__cause__, RuntimeError)


def test_a_dropped_file_named_like_a_named_module_is_refused_naming_both(
    tmp_path: pathlib.Path,
) -> None:
    dropped = _drop(tmp_path, "valid.py")

    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert "fixture_plugins.valid" in refused.value.user_message
    assert str(dropped) in refused.value.user_message


def test_a_dropped_file_does_not_shadow_an_installed_module(
    tmp_path: pathlib.Path,
) -> None:
    """It is imported from where it lies rather than through `sys.path`, so dropping a
    file called `json.py` into the folder cannot change what `import json` means."""
    _drop(tmp_path, "json.py")

    load_plugins([], folder=tmp_path)

    assert sys.modules["json"].__name__ == "json"
    assert not hasattr(sys.modules["json"], "extend")


def test_a_contract_version_cora_does_not_offer_is_refused_naming_both() -> None:
    """Read before `extend` is called, so a plugin cora will not have never runs."""
    with pytest.raises(PluginLoadError) as refused:
        load_plugin("fixture_plugins.wrong_contract")

    assert "fixture_plugins.wrong_contract" in refused.value.user_message
    assert "99" in refused.value.user_message
    assert str(CONTRACT) in refused.value.user_message
