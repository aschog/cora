import re
from dataclasses import dataclass, replace
from datetime import date

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal

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
    rose: bool = False

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
    cora: Host,
    exercise: str | None = None,
    since: str | None = None,
    detail: bool = False,
) -> str:
    sessions = _risen(_sessions(cora))
    if exercise:
        sessions = _only(sessions, exercise)
    if since:
        sessions = [session for session in sessions if session.day >= _day(since)]
    if not sessions:
        narrowed = (f" with {exercise}" if exercise else "") + (
            f" since {since}" if since else ""
        )
        return f"No workout logged{narrowed}."
    if detail:
        return "\n\n".join(_detailed(session) for session in sessions)
    return "\n".join(_named(session) for session in sessions)


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


def _risen(sessions: list[Session]) -> list[Session]:
    # as `train` marks ↑: more volume, or a heavier load, than the previous session of
    # that exercise — and reps where a bodyweight load has no volume
    last: dict[str, tuple[float, float]] = {}
    risen = []
    for session in sessions:
        marked = []
        for movement in session.movements:
            measure = (
                movement.volume if movement.volume is not None else movement.reps,
                movement.load.value,
            )
            before = last.get(movement.name.casefold())
            rose = before is not None and (
                measure[0] > before[0] or measure[1] > before[1]
            )
            last[movement.name.casefold()] = measure
            marked.append(replace(movement, rose=rose))
        risen.append(replace(session, movements=tuple(marked)))
    return risen


def _only(sessions: list[Session], exercise: str) -> list[Session]:
    wanted = exercise.casefold()
    kept = [
        replace(
            session,
            movements=tuple(
                m for m in session.movements if m.name.casefold() == wanted
            ),
        )
        for session in sessions
    ]
    return [session for session in kept if session.movements]


def _day(since: str) -> date:
    try:
        return date.fromisoformat(since)
    except ValueError as error:
        raise ToolRefusal(
            f"since must be a day as YYYY-MM-DD, not {since!r}"
        ) from error


def _named(session: Session) -> str:
    names = dict.fromkeys(movement.name for movement in session.movements)
    return f"{session.day.isoformat()}: " + " · ".join(names)


def _detailed(session: Session) -> str:
    lines = [f"- {_line(movement)}" for movement in session.movements]
    return "\n".join([session.day.isoformat(), *lines])


def _line(movement: Movement) -> str:
    parts = [str(movement.load), _shown(movement.sets), f"{movement.reps} reps"]
    if movement.volume is not None:
        parts.append(f"{_number(movement.volume)} kg")
    return f"{movement.name} — " + " · ".join(parts) + (" ↑" if movement.rose else "")


def _shown(sets: tuple[int, ...]) -> str:
    if not sets:
        return "no sets"
    if len(set(sets)) == 1:
        return f"{len(sets)}x{sets[0]}"
    return "+".join(str(reps) for reps in sets)
