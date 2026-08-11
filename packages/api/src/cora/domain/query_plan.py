from dataclasses import dataclass

from cora.domain.metadata_filter import MetadataFilter


@dataclass(frozen=True)
class QueryPlan:
    queries: tuple[str, ...]
    metadata_filter: MetadataFilter | None = None
