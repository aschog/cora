"""Finding the plugins a deployment asked for, and refusing the ones it cannot have."""

import importlib
import importlib.machinery
import importlib.util
import pathlib
import sys
from collections.abc import Iterable
from types import ModuleType

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.engine.validation import CORA
from cora.ports.host import CONTRACT, Extension, name_of

EXTEND = "extend"
DECLARED = "CONTRACT"
"""What a plugin names to ask for a version of the contract. Read before `extend` is
called, because refusing a plugin whose code has already run is not refusing it."""

DROPPED = "cora_dropped"
"""The namespace a file dropped in the folder is imported under.

It has to be imported under *some* name that outlives the import: a module absent from
`sys.modules` cannot resolve its own annotations, so an ordinary dataclass in a dropped
file fails on code that is correct everywhere else. Under a namespace of cora's own
rather than under the file's own stem, so dropping `json.py` in the folder still cannot
change what `import json` means anywhere.
"""

SUFFIX = ".py"
INIT = "__init__.py"
"""What makes a dropped directory a plugin: the same marker that makes it a package."""
SKIPPED = ("_", ".")
"""How an entry in the folder says it is not a plugin: `__init__.py` and anything an
author named as private, and anything hidden — a volume that has been near a Mac keeps
`._name.py` beside every file, and one of those refuses the whole deployment."""


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
    _reject_a_stem_that_is_not_a_name(dropped)
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
            module_path,
            f"the plugin module raised {type(exc).__name__} while importing",
        ) from exc
    except Exception as exc:
        raise PluginLoadError(
            module_path,
            f"the plugin module raised {type(exc).__name__} while importing",
        ) from exc
    return _extension(module, name=module_path, source=module_path)


def load_file(path: pathlib.Path) -> Extension:
    """One plugin dropped in as a file or a package directory, with no packaging at all.

    Imported from where it lies rather than through `sys.path`, and under a namespace
    of cora's own: nothing dropped in the folder can shadow an installed module of the
    same name, and it can still resolve its own annotations. A directory imports as a
    package whose path is the folder itself, so its own relative imports resolve as the
    author wrote them. Its name — a file's stem, a directory's own — is the plugin's,
    which is what heads its section of the brief and what its settings are named for.

    Raises:
        PluginLoadError: The path cannot be read as a plugin, failed to import, asks
            for a contract version cora does not offer, or defines no usable `extend`.
    """
    source = str(path)
    name = _dropped_name(path)
    location = path / INIT if path.is_dir() else path
    spec = importlib.util.spec_from_file_location(
        f"{DROPPED}.{name}",
        location,
        loader=_FreshSource(f"{DROPPED}.{name}", str(location)),
        submodule_search_locations=[source] if path.is_dir() else None,
    )
    if spec is None or spec.loader is None:
        raise PluginLoadError(source, "the file could not be read as a plugin")
    module = importlib.util.module_from_spec(spec)
    # Put back rather than deleted, so a plugin that fails leaves whatever was under
    # its name — a package's submodules included — exactly as it found it.
    displaced = {found: sys.modules.pop(found) for found in _under(spec.name)}
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        _restore(spec.name, displaced)
        raise PluginLoadError(
            source, f"the plugin file raised {type(exc).__name__} while importing"
        ) from exc
    return _extension(module, name=name, source=source)


class _FreshSource(importlib.machinery.SourceFileLoader):
    """A loader that always compiles the source it was pointed at.

    CPython validates a `.pyc` by whole-second mtime and size, so a plugin edited in
    the same second as its last load — same length, different code — would run the
    stale bytecode the cache kept. Statting is refused, which makes the loader skip
    the cache both ways: nothing is read from one, nothing is written into one. A
    package's *members* still import through Python's own finder and keep its caching,
    so a same-second same-size edit to one of those waits for the next second.
    """

    def path_stats(self, path: str) -> dict[str, float]:
        raise OSError("a dropped plugin is not bytecode-cached")


def _dropped_name(path: pathlib.Path) -> str:
    """A directory's name is taken whole: `stem` would read `acme.birds` as `acme`."""
    return path.name if path.is_dir() else path.stem


def _under(name: str) -> list[str]:
    prefix = f"{name}."
    return [found for found in sys.modules if found == name or found.startswith(prefix)]


def _restore(name: str, displaced: dict[str, ModuleType]) -> None:
    for found in _under(name):
        del sys.modules[found]
    sys.modules.update(displaced)


def _files_in(folder: pathlib.Path | None) -> tuple[pathlib.Path, ...]:
    """The folder's plugins, in name order. A folder that is not there holds none."""
    if folder is None or not folder.is_dir():
        return ()
    return tuple(
        sorted(
            path
            for path in folder.iterdir()
            if not path.name.startswith(SKIPPED)
            and (
                (path / INIT).is_file()
                if path.is_dir()
                else path.suffix == SUFFIX and path.is_file()
            )
        )
    )


def folder_signature(folder: pathlib.Path | None) -> tuple[object, ...]:
    """One cheap reading of what the folder holds, for telling two moments apart.

    Every plugin entry by name, stamp and — for a package — every `.py` inside it, so
    a drop, a delete and an edit each move it. It is compared and never parsed, and it
    races the folder by design: an entry that vanishes mid-read makes a difference,
    which is all a difference has to do.
    """
    return tuple(
        (path.name, _members(path)) if path.is_dir() else (path.name, _stamp(path))
        for path in _files_in(folder)
    )


def _members(package: pathlib.Path) -> tuple[object, ...]:
    return tuple(
        sorted(
            (str(inner.relative_to(package)), _stamp(inner))
            for inner in package.rglob(f"*{SUFFIX}")
        )
    )


def _stamp(path: pathlib.Path) -> tuple[object, ...]:
    try:
        found = path.stat()
    except OSError:
        return ("gone",)
    return (found.st_mtime_ns, found.st_size)


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


def _reject_a_stem_that_is_not_a_name(dropped: tuple[pathlib.Path, ...]) -> None:
    """Refuse a file whose stem cannot serve as the plugin's name.

    Four things are named by it, and two of them cannot carry an arbitrary string: the
    settings prefix has to be spellable in a shell, and `name_of` reads everything after
    the last dot — so `acme.birds.py` would be `birds` to every reader and `acme.birds`
    to the check meant to stop a second `birds`.

    Raises:
        ConfigurationError: The stem is not an identifier.
    """
    for path in dropped:
        if not _dropped_name(path).isidentifier():
            raise ConfigurationError(
                f"'{path.name}' cannot name a plugin: a name heads a section of the "
                "brief and spells a variable in the environment, so it has to be a "
                "plain identifier. Rename it."
            )


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
    it exactly as two named modules do, which is why both sources are read here — and
    cora's own name is taken, a plugin holding it being handed cora's own registrations
    as its own.
    """
    seen: dict[str, str] = {}
    for name, source in (
        *((name_of(module), module) for module in named),
        *((_dropped_name(path), str(path)) for path in dropped),
    ):
        if name == CORA:
            raise ConfigurationError(
                f"'{source}' is named '{CORA}', which is what cora registers its own "
                "under. Rename it."
            )
        first = seen.get(name)
        if first is not None:
            raise ConfigurationError(
                f"'{first}' and '{source}' are both named '{name}', so their "
                "instructions and their settings cannot be told apart. Rename one."
            )
        seen[name] = source
