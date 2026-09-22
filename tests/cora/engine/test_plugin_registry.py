import pathlib

import pytest

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.engine.plugin_registry import folder_signature, load_plugin, load_plugins
from cora.ports.host import CONTRACT


def test_loading_a_plugin_hands_back_the_module_and_its_extend() -> None:
    loaded = load_plugin("fixture_plugins.valid")

    assert loaded.module == "fixture_plugins.valid"
    assert callable(loaded.extend)


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


def test_a_file_dropped_in_the_folder_is_loaded_under_its_stem(
    tmp_path: pathlib.Path,
) -> None:
    dropped = _drop(tmp_path, "field_notes.py")

    loaded = load_plugins([], folder=tmp_path)

    assert [(each.module, each.source) for each in loaded] == [
        ("field_notes", str(dropped))
    ]


def test_the_folder_is_read_in_name_order_after_the_modules_named(
    tmp_path: pathlib.Path,
) -> None:
    _drop(tmp_path, "zebra.py")
    _drop(tmp_path, "aardvark.py")

    loaded = load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert [each.module for each in loaded] == [
        "fixture_plugins.valid",
        "aardvark",
        "zebra",
    ]


def test_a_dropped_file_named_like_a_named_module_is_refused_naming_both(
    tmp_path: pathlib.Path,
) -> None:
    dropped = _drop(tmp_path, "valid.py")

    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert "fixture_plugins.valid" in refused.value.user_message
    assert str(dropped) in refused.value.user_message


def test_a_contract_version_cora_does_not_offer_is_refused_naming_both() -> None:
    with pytest.raises(PluginLoadError) as refused:
        load_plugin("fixture_plugins.wrong_contract")

    assert "fixture_plugins.wrong_contract" in refused.value.user_message
    assert "99" in refused.value.user_message
    assert str(CONTRACT) in refused.value.user_message


def _drop_package(
    folder: pathlib.Path, name: str, init: str = DROPPED, **modules: str
) -> pathlib.Path:
    package = folder / name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(init)
    for module, source in modules.items():
        (package / f"{module}.py").write_text(source)
    return package


RELATIVE_IMPORT = """\
from cora.ports.host import Host

from .notes import FIELD


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about " + FIELD + ".", scope=FIELD)
"""


def test_a_package_dropped_in_the_folder_is_loaded_under_its_folder_name(
    tmp_path: pathlib.Path,
) -> None:
    package = _drop_package(tmp_path, "field_notes")

    loaded = load_plugins([], folder=tmp_path)

    assert [(each.module, each.source) for each in loaded] == [
        ("field_notes", str(package))
    ]


def test_a_dropped_packages_relative_imports_resolve(tmp_path: pathlib.Path) -> None:
    _drop_package(
        tmp_path, "field_notes", init=RELATIVE_IMPORT, notes='FIELD = "birds"\n'
    )

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == "field_notes"


def test_a_symlinked_package_is_a_plugin_like_any_other(
    tmp_path: pathlib.Path,
) -> None:
    target = _drop_package(tmp_path / "elsewhere", "field_notes")
    folder = tmp_path / "plugins"
    folder.mkdir()
    (folder / "field_notes").symlink_to(target)

    (loaded,) = load_plugins([], folder=folder)
    assert loaded.module == "field_notes"
    assert loaded.source == str(folder / "field_notes")

    before = folder_signature(folder)
    (target / "__init__.py").write_text(f"{DROPPED}\n# revised\n")
    assert folder_signature(folder) != before
