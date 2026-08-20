"""Loading the plugins a deployment named, and refusing the ones it cannot have."""

import importlib
from collections.abc import Iterable

from jsonschema import Draft202012Validator, SchemaError

from cora.domain.errors import PluginLoadError
from cora.engine.plugin_set import PluginSet
from cora.ports.plugin import Plugin


def load_plugins(module_paths: Iterable[str]) -> PluginSet:
    """Load every named plugin, in the order it was named.

    Each module is named in its own refusal, so one bad entry in a list of three points
    at itself rather than at the list.

    Raises:
        PluginLoadError: One of the modules could not be loaded.
        ConfigurationError: The modules load but the set they make cannot be composed —
            a module named twice, or two plugins offering one tool name.
    """
    return PluginSet(tuple((path, load_plugin(path)) for path in module_paths))


def load_plugin(module_path: str) -> Plugin:
    """The `PLUGIN` bundle a module contributes, checked before it is trusted.

    A plugin is arbitrary code cora was told to import, so every assumption about the
    bundle is stated as a refusal here rather than met later as an attribute error.

    Raises:
        PluginLoadError: The module is missing, failed to import, defines no `PLUGIN`,
            or defines one that is not usable — a blank name, two tools sharing a name,
            a tool that cannot be called, or a parameter schema that is not valid JSON
            Schema.
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
    if not hasattr(module, "PLUGIN"):
        raise PluginLoadError(module_path, "the module defines no PLUGIN bundle")
    bundle = module.PLUGIN
    if not isinstance(bundle, Plugin):
        raise PluginLoadError(module_path, "PLUGIN is not a Plugin bundle")
    _validate_bundle(module_path, bundle)
    return bundle


def _validate_bundle(module_path: str, bundle: Plugin) -> None:
    if not bundle.name.strip():
        raise PluginLoadError(module_path, "the plugin name is blank")
    names = [tool.name for tool in bundle.tools]
    if len(set(names)) != len(names):
        raise PluginLoadError(module_path, "two tools share the same name")
    for tool in bundle.tools:
        if not callable(tool.run):
            raise PluginLoadError(
                module_path, f"tool '{tool.name}' has no callable run"
            )
        try:
            Draft202012Validator.check_schema(tool.parameter_schema)
        except SchemaError as exc:
            raise PluginLoadError(
                module_path, f"tool '{tool.name}' has an invalid parameter schema"
            ) from exc
