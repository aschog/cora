from dataclasses import dataclass


@dataclass(frozen=True)
class MetadataFilter:
    field: str
    value: str
