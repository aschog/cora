"""Loading the plugin modules a deployment named, and refusing the ones it cannot."""

import importlib
from collections.abc import Iterable

from cora.domain.errors import ConfigurationError, PluginLoadError
from cora.ports.host import Extension

EXTEND = "extend"


def load_plugins(module_paths: Iterable[str]) -> tuple[Extension, ...]:
    """Import every named plugin, in the order it was named.

    Importing is all that happens here: what a plugin contributes is registered later,
    against a host, because a host is made of parts an assembled app holds. Each module
    is named in its own refusal, so one bad entry in a list of three points at itself.

    Raises:
        PluginLoadError: A module is missing, failed to import, or defines no `extend`.
        ConfigurationError: The same module was named twice, or two modules end in the
            same name and so cannot be told apart.
    """
    named = tuple(module_paths)
    _reject_a_module_named_twice(named)
    _reject_two_named_alike(named)
    return tuple(load_plugin(path) for path in named)


def load_plugin(module_path: str) -> Extension:
    """One plugin module, checked as far as importing can check it.

    A plugin is arbitrary code cora was told to import, so every assumption about the
    module is stated as a refusal here rather than met later as an attribute error.

    Raises:
        PluginLoadError: The module is missing, failed to import, defines no `extend`,
            or defines one that cannot be called.
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
    extend = getattr(module, EXTEND, None)
    if extend is None:
        raise PluginLoadError(module_path, "the module defines no extend(cora)")
    if not callable(extend):
        raise PluginLoadError(module_path, "the module's extend is not callable")
    return Extension(module=module_path, extend=extend)


def _reject_a_module_named_twice(named: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for module in named:
        if module in seen:
            raise ConfigurationError(
                f"'{module}' is listed twice. Name each plugin once."
            )
        seen.add(module)


def _reject_two_named_alike(named: tuple[str, ...]) -> None:
    """Refuse two plugins whose module paths end in the same name.

    A name is what tells two plugins apart: it heads their sections of the brief, and
    their settings are named for it.
    """
    seen: dict[str, str] = {}
    for module in named:
        last = module.rsplit(".", 1)[-1]
        first = seen.get(last)
        if first is not None:
            raise ConfigurationError(
                f"'{first}' and '{module}' are both named '{last}', so their "
                "instructions and their settings cannot be told apart. Rename one."
            )
        seen[last] = module
