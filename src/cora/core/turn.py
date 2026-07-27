from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "assistant"]
    text: str
