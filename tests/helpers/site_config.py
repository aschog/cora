import yaml

import workspace

CONFIG = workspace.ROOT / "mkdocs.yml"


class Tolerant(yaml.SafeLoader):
    pass


Tolerant.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: suffix
)


def config() -> dict[str, object]:
    return yaml.load(CONFIG.read_text(), Loader=Tolerant)


def nav_pages(entry: object) -> list[str]:
    if isinstance(entry, str):
        return [entry]
    if isinstance(entry, dict):
        return [page for value in entry.values() for page in nav_pages(value)]
    if isinstance(entry, list):
        return [page for item in entry for page in nav_pages(item)]
    return []
