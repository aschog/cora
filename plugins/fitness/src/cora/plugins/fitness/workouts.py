import re
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

from cora.ports.host import Host

NUMBER = r"\d+(?:\.\d+)?"
DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})\.[A-Za-z0-9]+$")
HEADING = re.compile(
    rf"^#\s+(?P<name>.+?)\s+(?:(?P<kg>{NUMBER})\s*kg|bw(?:\+(?P<bw>{NUMBER}))?)$"
)
REPEATED = re.compile(r"^(\d+)\s+sets\s+of\s+(\d+)$")
LISTED = re.compile(r"^sets\s+of\s+(\d+(?:\s*/\s*\d+)+)$")
TIMED = re.compile(rf"^{NUMBER}\s*min\s*·\s*(\d+)\s*/\s*(\d+)$")


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

    @property
    def reps(self) -> int:
        return sum(self.sets)

    @property
    def volume(self) -> float | None:
        return self.load.value * self.reps if self.load.kind == "kg" else None


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
            continue
        if not movements:
            raise LogError(name, number, "text before the first heading")
        sets = _sets(line)
        if sets is None:
            movements[-1] = replace(movements[-1], notes=(*movements[-1].notes, raw))
        elif movements[-1].sets:
            raise LogError(name, number, "a movement has one set line")
        else:
            movements[-1] = replace(movements[-1], sets=sets)
    return Session(day, tuple(movements))


def _sets(line: str) -> tuple[int, ...] | None:
    if found := REPEATED.match(line):
        return (int(found[2]),) * int(found[1])
    if found := LISTED.match(line):
        return tuple(int(reps) for reps in re.split(r"\s*/\s*", found[1]))
    if found := TIMED.match(line):
        return (int(found[1]) + int(found[2]),)
    return None


def _number(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:.1f}"


def list_workouts(
    cora: Host, exercise: str | None = None, since: str | None = None
) -> list[dict[str, Any]] | str:
    return [_listed(session) for session in _sessions(cora)]


def _sessions(cora: Host) -> list[Session]:
    by_day: dict[date, list[Movement]] = {}
    for document in cora.documents.all():
        day = _day_of(document.name)
        if day is None:
            continue
        try:
            parsed = parse_session(document.text, day, document.name)
        except LogError as refused:
            cora.show(f"skipped {document.name}", detail=str(refused), failed=True)
            continue
        by_day.setdefault(day, []).extend(parsed.movements)
    return [Session(day, tuple(moved)) for day, moved in sorted(by_day.items())]


def _day_of(name: str) -> date | None:
    dated = DATED.match(name)
    try:
        return date.fromisoformat(dated[1]) if dated else None
    except ValueError:
        return None


def _listed(session: Session) -> dict[str, Any]:
    return {
        "date": session.day.isoformat(),
        "movements": [
            {
                "name": movement.name,
                "load": str(movement.load),
                "sets": list(movement.sets),
                "reps": movement.reps,
                "volume_kg": movement.volume,
            }
            for movement in session.movements
        ],
    }
