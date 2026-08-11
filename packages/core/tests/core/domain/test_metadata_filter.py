import dataclasses

import pytest

from cora.core.domain.metadata_filter import MetadataFilter


def test_metadata_filters_are_equal_by_content() -> None:
    assert MetadataFilter(field="source", value="protein.md") == MetadataFilter(
        field="source", value="protein.md"
    )
    assert MetadataFilter(field="source", value="protein.md") != MetadataFilter(
        field="source", value="energy_balance.md"
    )
    assert MetadataFilter(field="source", value="protein.md") != MetadataFilter(
        field="section", value="protein.md"
    )


def test_metadata_filter_is_immutable() -> None:
    metadata_filter = MetadataFilter(field="source", value="protein.md")

    with pytest.raises(dataclasses.FrozenInstanceError):
        metadata_filter.value = "changed"  # ty: ignore[invalid-assignment]
