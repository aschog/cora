import importlib

from docchat.plugin import Plugin


def load_plugin(module_path: str) -> Plugin:
    module = importlib.import_module(module_path)
    return module.PLUGIN
