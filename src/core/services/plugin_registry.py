import importlib

from jsonschema import Draft202012Validator, SchemaError

from core.errors import PluginLoadError
from core.ports.plugin import Plugin


def load_plugin(module_path: str) -> Plugin:
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
    if not bundle.system_prompt.strip():
        raise PluginLoadError(module_path, "the system prompt is blank")
    if not bundle.tools:
        raise PluginLoadError(module_path, "the bundle provides no tools")
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
