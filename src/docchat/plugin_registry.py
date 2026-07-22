import importlib

from docchat.errors import PluginLoadError
from docchat.plugin import Plugin


def load_plugin(module_path: str) -> Plugin:
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise PluginLoadError(module_path, "the plugin module was not found") from exc
    return module.PLUGIN
