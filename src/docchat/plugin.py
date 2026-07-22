from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameter_schema: dict[str, Any]
    run: Callable[..., Any]
