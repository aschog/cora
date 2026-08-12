import dataclasses

import pytest

from cora.domain.metadata_filter import MetadataFilter
from cora.domain.query_plan import QueryPlan


def test_query_plans_are_equal_by_content() -> None:
    assert QueryPlan(queries=("a", "b")) == QueryPlan(queries=("a", "b"))
    assert QueryPlan(queries=("a", "b")) != QueryPlan(queries=("a", "c"))


def test_query_plan_carries_an_optional_metadata_filter_defaulting_to_none() -> None:
    assert QueryPlan(queries=("a",)).metadata_filter is None

    plan = QueryPlan(
        queries=("a",), metadata_filter=MetadataFilter(field="source", value="p.md")
    )
    assert plan.metadata_filter == MetadataFilter(field="source", value="p.md")


def test_query_plan_is_immutable() -> None:
    plan = QueryPlan(queries=("a",))

    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.queries = ("b",)  # ty: ignore[invalid-assignment]
