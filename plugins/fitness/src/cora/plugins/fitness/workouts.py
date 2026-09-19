import re
from dataclasses import dataclass
from datetime import date

NUMBER = r"\d+(?:\.\d+)?"
HEADING = re.compile(
    rf"^#\s+(?P<name>.+?)\s+(?:(?P<kg>{NUMBER})\s*kg|bw(?:\+(?P<bw>{NUMBER}))?)$"
)


class LogError(Exception):
    def __init__(self, name: str, line: int, message: str) -> None:
        super().__init__(f"{name}:{line}: {message}")
        self.name, self.line, self.message = name, line, message


@dataclass(frozen=True)
class Load:
    kind: str
    value: float = 0.0

    def __str__(self) -> str:
        if self.kind == "kg":
            return f"{_number(self.value)} kg"
        return f"bw+{_number(self.value)}" if self.value else "bw"


@dataclass(frozen=True)
class Movement:
    name: str
    load: Load
    sets: tuple[int, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Session:
    day: date
    movements: tuple[Movement, ...]


def parse_session(text: str, day: date, name: str = "<session>") -> Session:
    movements: list[Movement] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            found = HEADING.match(line)
            if not found:
                raise LogError(
                    name, number, "a heading ends with a load: <n> kg, bw or bw+<n>"
                )
            load = (
                Load("kg", float(found["kg"]))
                if found["kg"]
                else Load("bw", float(found["bw"] or 0))
            )
            movements.append(Movement(found["name"], load))
    return Session(day, tuple(movements))


def _number(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"
