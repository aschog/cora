"""`mkdocs.yml` as data. Two suites read the nav for different reasons, so the loader
and the walk live here rather than once per suite.
"""

import yaml

import workspace

CONFIG = workspace.ROOT / "mkdocs.yml"


class Tolerant(yaml.SafeLoader):
    """mkdocs writes `!!python/name:` tags that a safe loader refuses; the guards read
    the config as data and never call what those tags name."""


Tolerant.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: suffix
)


def config() -> dict[str, object]:
    return yaml.load(CONFIG.read_text(), Loader=Tolerant)


def nav_pages(entry: object) -> list[str]:
    """Every page the nav names, however deeply a section nests it."""
    if isinstance(entry, str):
        return [entry]
    if isinstance(entry, dict):
        return [page for value in entry.values() for page in nav_pages(value)]
    if isinstance(entry, list):
        return [page for item in entry for page in nav_pages(item)]
    return []
