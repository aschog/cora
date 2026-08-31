"""Finding the plugins a deployment asked for, and refusing the ones it cannot have."""

import importlib
import importlib.util
import pathlib
from collections.abc import Iterable
from types import ModuleType

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.ports.host import CONTRACT, Extension

EXTEND = "extend"
DECLARED = "CONTRACT"
"""What a plugin names to ask for a version of the contract. Read before `extend` is
called, because refusing a plugin whose code has already run is not refusing it."""

SUFFIX = ".py"
PRIVATE = "_"
"""A file the folder does not offer as a plugin: `__init__.py`, and anything an author
named as private. Everything else in there was dropped in to be loaded."""


def load_plugins(
    module_paths: Iterable[str], folder: pathlib.Path | None = None
) -> tuple[Extension, ...]:
    """Every plugin this deployment asked for, from both places it can ask.

    The named modules first, then the folder's files in name order: load order is the
    only precedence there is, so it is one a deployment can predict. Each plugin is
    named in its own refusal, so one bad entry among three points at itself.

    Args:
        folder: Where a plugin may be dropped as a single file. Absent or missing, the
            deployment simply has none.

    Raises:
        PluginLoadError: A plugin is missing, failed to import, asks for a contract
            version cora does not offer, or defines no `extend`.
        ConfigurationError: The same module was named twice, or two plugins end in the
            same name and so cannot be told apart.
    """
    named = tuple(module_paths)
    dropped = _files_in(folder)
    _reject_a_module_named_twice(named)
    _reject_two_named_alike(named, dropped)
    return (
        *(load_plugin(path) for path in named),
        *(load_file(path) for path in dropped),
    )


def load_plugin(module_path: str) -> Extension:
    """One named plugin module, checked as far as importing can check it.

    A plugin is arbitrary code cora was told to import, so every assumption about the
    module is stated as a refusal here rather than met later as an attribute error.

    Raises:
        PluginLoadError: The module is missing, failed to import, asks for a contract
            version cora does not offer, defines no `extend`, or defines one that
            cannot be called.
    """
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        if exc.name == module_path or module_path.startswith(f"{exc.name}."):
            raise PluginLoadError(
                module_path, "the plugin module was not found"
            ) from exc
        raise PluginLoadError(
            module_path, "the plugin module failed to import"
        ) from exc
    except Exception as exc:
        raise PluginLoadError(
            module_path, "the plugin module failed to import"
        ) from exc
    return _extension(module, name=module_path, source=module_path)


def load_file(path: pathlib.Path) -> Extension:
    """One plugin dropped in as a single file, with no packaging at all.

    Imported from where it lies rather than through `sys.path`, and left out of the
    imported modules: a file dropped in a folder cannot then shadow an installed module
    of the same name. Its stem is its name, as a module's last segment is — which is
    what heads its section of the brief and what its settings are named for.

    Raises:
        PluginLoadError: The file cannot be read as a plugin, failed to import, asks
            for a contract version cora does not offer, or defines no usable `extend`.
    """
    source = str(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise PluginLoadError(source, "the file could not be read as a plugin")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise PluginLoadError(source, "the plugin file failed to import") from exc
    return _extension(module, name=path.stem, source=source)


def _files_in(folder: pathlib.Path | None) -> tuple[pathlib.Path, ...]:
    """The folder's plugins, in name order. A folder that is not there holds none."""
    if folder is None or not folder.is_dir():
        return ()
    return tuple(
        sorted(
            path
            for path in folder.glob(f"*{SUFFIX}")
            if path.is_file() and not path.name.startswith(PRIVATE)
        )
    )


def _extension(module: ModuleType, *, name: str, source: str) -> Extension:
    """What the module has to prove before anything of it is kept.

    Raises:
        PluginLoadError: It asks for a version cora does not offer, defines no
            `extend`, or defines one that cannot be called.
    """
    wanted = getattr(module, DECLARED, CONTRACT)
    if wanted != CONTRACT:
        raise PluginLoadError(
            source,
            f"it asks for contract version {wanted!r}, and cora offers {CONTRACT}",
        )
    extend = getattr(module, EXTEND, None)
    if extend is None:
        raise PluginLoadError(source, "the module defines no extend(cora)")
    if not callable(extend):
        raise PluginLoadError(source, "the module's extend is not callable")
    return Extension(module=name, extend=extend, source=source)


def _reject_a_module_named_twice(named: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for module in named:
        if module in seen:
            raise ConfigurationError(
                f"'{module}' is listed twice. Name each plugin once."
            )
        seen.add(module)


def _reject_two_named_alike(
    named: tuple[str, ...], dropped: tuple[pathlib.Path, ...]
) -> None:
    """Refuse two plugins ending in the same name, whichever source each came from.

    A name is what tells two plugins apart: it heads their sections of the brief, and
    their settings are named for it. A file dropped beside a named module collides with
    it exactly as two named modules do, which is why both sources are read here.
    """
    seen: dict[str, str] = {}
    for name, source in (
        *((module.rsplit(".", 1)[-1], module) for module in named),
        *((path.stem, str(path)) for path in dropped),
    ):
        first = seen.get(name)
        if first is not None:
            raise ConfigurationError(
                f"'{first}' and '{source}' are both named '{name}', so their "
                "instructions and their settings cannot be told apart. Rename one."
            )
        seen[name] = source
