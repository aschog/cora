import importlib

from docchat.errors import PluginLoadError
from docchat.plugin import Plugin


def load_plugin(module_path: str) -> Plugin:
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise PluginLoadError(module_path, "the plugin module was not found") from exc
    except Exception as exc:
        raise PluginLoadError(
            module_path, "the plugin module failed to import"
        ) from exc
    bundle = getattr(module, "PLUGIN", None)
    if not isinstance(bundle, Plugin):
        raise PluginLoadError(module_path, "the module defines no PLUGIN bundle")
    _validate_bundle(module_path, bundle)
    return bundle


def _validate_bundle(module_path: str, bundle: Plugin) -> None:
    if not bundle.system_prompt.strip():
        raise PluginLoadError(module_path, "the system prompt is blank")
