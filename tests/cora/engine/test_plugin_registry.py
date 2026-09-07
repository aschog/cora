import pathlib
import sys

import pytest

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.engine.plugin_registry import load_plugin, load_plugins
from cora.engine.validation import CORA
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

    assert "ModuleNotFoundError while importing" in excinfo.value.user_message
    assert "was not found" not in excinfo.value.user_message, (
        "the plugin is there; what it imports is not, and the two refusals are "
        "different sentences because they are different things to fix"
    )


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
    assert "RuntimeError" in refused.value.user_message, (
        "the operator reads the message, not the cause: `serve` prints "
        "`user_message` and raises `SystemExit` from None, so a reason kept only on "
        "`__cause__` is a reason nobody is shown"
    )


def test_a_dropped_file_named_like_a_named_module_is_refused_naming_both(
    tmp_path: pathlib.Path,
) -> None:
    dropped = _drop(tmp_path, "valid.py")

    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert "fixture_plugins.valid" in refused.value.user_message
    assert str(dropped) in refused.value.user_message


DEFERRED_ANNOTATIONS = """\
from __future__ import annotations

from dataclasses import dataclass

from cora.ports.host import Host


@dataclass(frozen=True)
class Sighting:
    species: str
    count: int


def extend(cora: Host) -> None:
    cora.register_instructions("Answer about birds.", scope="birds")
"""


def test_a_dropped_file_may_write_ordinary_python(tmp_path: pathlib.Path) -> None:
    """A dataclass under deferred annotations resolves its fields through the imported
    modules, so a file imported into nowhere fails on code that is correct everywhere
    else — and the refusal would blame the author for cora's own loading."""
    _drop(tmp_path, "field_notes.py", DEFERRED_ANNOTATIONS)

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == "field_notes"


NOT_A_NAME = ["acme.birds.py", "field-notes.py", "2birds.py"]


@pytest.mark.parametrize("filename", NOT_A_NAME)
def test_a_dropped_file_whose_stem_is_not_a_name_is_refused(
    tmp_path: pathlib.Path, filename: str
) -> None:
    """A plugin's name has to be one: it heads a section of the brief and it spells a
    variable in the environment. `acme.birds.py` would be read as `birds` by everything
    downstream and as `acme.birds` by the check meant to stop two of them, and
    `field-notes.py` asks for a `CORA_PLUGIN_FIELD-NOTES_` no shell will set."""
    _drop(tmp_path, filename)

    with pytest.raises(ConfigurationError) as refused:
        load_plugins([], folder=tmp_path)

    assert filename in refused.value.user_message


def test_a_plugin_may_not_take_coras_own_name(tmp_path: pathlib.Path) -> None:
    """Cora registers under a name of its own, so a plugin holding it would be handed
    cora's own screen as its registrations — and cora would report that nothing screens
    what the user types while that plugin's screen was running."""
    _drop(tmp_path, f"{CORA}.py")

    with pytest.raises(ConfigurationError) as refused:
        load_plugins([], folder=tmp_path)

    assert CORA in refused.value.user_message


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
    """A directory holding `__init__.py` is one plugin, exactly as a file is: named
    for the folder, sourced from where it lies, no packaging at all."""
    package = _drop_package(tmp_path, "field_notes")

    loaded = load_plugins([], folder=tmp_path)

    assert [(each.module, each.source) for each in loaded] == [
        ("field_notes", str(package))
    ]


def test_a_directory_without_init_is_not_a_plugin(tmp_path: pathlib.Path) -> None:
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "readme.py").write_text(DROPPED)

    assert load_plugins([], folder=tmp_path) == ()


@pytest.mark.parametrize("name", ["_drafts", ".hidden"])
def test_a_hidden_or_private_directory_is_not_a_plugin(
    tmp_path: pathlib.Path, name: str
) -> None:
    _drop_package(tmp_path, name)

    assert load_plugins([], folder=tmp_path) == ()


def test_a_dropped_packages_relative_imports_resolve(tmp_path: pathlib.Path) -> None:
    """The folder is the package, so `from . import` inside it works as the author
    wrote it — flattening is not the price of dropping in."""
    _drop_package(
        tmp_path, "field_notes", init=RELATIVE_IMPORT, notes='FIELD = "birds"\n'
    )

    (loaded,) = load_plugins([], folder=tmp_path)

    assert loaded.module == "field_notes"


def test_a_dropped_package_does_not_shadow_an_installed_module(
    tmp_path: pathlib.Path,
) -> None:
    _drop_package(tmp_path, "json")

    load_plugins([], folder=tmp_path)

    assert sys.modules["json"].__name__ == "json"
    assert not hasattr(sys.modules["json"], "extend")


def test_a_package_that_fails_to_import_is_refused_by_its_folder_name(
    tmp_path: pathlib.Path,
) -> None:
    package = _drop_package(tmp_path, "broken", init="raise RuntimeError('boom')\n")

    with pytest.raises(PluginLoadError) as refused:
        load_plugins([], folder=tmp_path)

    assert str(package) in refused.value.user_message
    assert "RuntimeError" in refused.value.user_message


def test_a_failed_package_leaves_sys_modules_as_it_found_it(
    tmp_path: pathlib.Path,
) -> None:
    """A package imports its siblings under its own name before it fails, and a stale
    entry left behind would be what the next load of that name quietly gets."""
    _drop_package(
        tmp_path,
        "birds",
        init="from .notes import FIELD\nraise RuntimeError('boom')\n",
        notes='FIELD = "birds"\n',
    )

    with pytest.raises(PluginLoadError):
        load_plugins([], folder=tmp_path)

    assert not [name for name in sys.modules if "birds" in name]


@pytest.mark.parametrize("name", ["acme.birds", "field-notes", "2birds"])
def test_a_package_whose_folder_name_is_not_a_name_is_refused(
    tmp_path: pathlib.Path, name: str
) -> None:
    """`acme.birds` is the trap: a directory's `stem` reads it as `acme`, so the check
    has to read the folder's name whole."""
    _drop_package(tmp_path, name)

    with pytest.raises(ConfigurationError) as refused:
        load_plugins([], folder=tmp_path)

    assert name in refused.value.user_message


def test_a_dropped_package_named_like_a_named_module_is_refused_naming_both(
    tmp_path: pathlib.Path,
) -> None:
    package = _drop_package(tmp_path, "valid")

    with pytest.raises(ConfigurationError) as refused:
        load_plugins(["fixture_plugins.valid"], folder=tmp_path)

    assert "fixture_plugins.valid" in refused.value.user_message
    assert str(package) in refused.value.user_message


def test_a_package_that_registers_nothing_is_refused(tmp_path: pathlib.Path) -> None:
    package = _drop_package(tmp_path, "field_notes", init="FIELD = 'birds'\n")

    with pytest.raises(PluginLoadError) as refused:
        load_plugins([], folder=tmp_path)

    assert str(package) in refused.value.user_message
    assert "defines no extend" in refused.value.user_message


def test_a_package_asking_for_a_contract_cora_does_not_offer_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    package = _drop_package(tmp_path, "field_notes", init=f"CONTRACT = 99\n{DROPPED}")

    with pytest.raises(PluginLoadError) as refused:
        load_plugins([], folder=tmp_path)

    assert str(package) in refused.value.user_message
    assert "99" in refused.value.user_message
    assert str(CONTRACT) in refused.value.user_message


NOT_A_VERSION = ["'1'", "None", "1.5"]


@pytest.mark.parametrize("declared", NOT_A_VERSION)
def test_a_contract_that_is_not_a_version_is_refused_legibly(
    tmp_path: pathlib.Path, declared: str
) -> None:
    """A version cora does not offer is a version cora does not offer, however it was
    written — and the refusal quotes it, so `'1'` is telling apart from `1`."""
    _drop(tmp_path, "field_notes.py", f"CONTRACT = {declared}\n{DROPPED}")

    with pytest.raises(PluginLoadError) as refused:
        load_plugins([], folder=tmp_path)

    assert declared in refused.value.user_message
