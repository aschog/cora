import re
from dataclasses import dataclass, replace
from datetime import date

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal

NUMBER = r"\d+(?:\.\d+)?"
DATED = re.compile(
    r"^(\d{4}-\d{2}-\d{2})(?:-\d{2}[-:]\d{2}[-:]\d{2}(?:-.*)?)?\.[A-Za-z0-9]+$"
)
HEADING = re.compile(
    rf"^#\s+(?P<name>.+?)\s+(?:(?P<kg>{NUMBER})\s*kg|bw(?:\+(?P<bw>{NUMBER}))?)$"
)
REPEATED = re.compile(r"^(\d+)\s+sets\s+of\s+(\d+)$")
LISTED = re.compile(r"^sets\s+of\s+(\d+(?:\s*/\s*\d+)+)$")
TIMED = re.compile(rf"^{NUMBER}\s*min\s*·\s*(\d+)\s*/\s*(\d+)$")
MOST_DETAILED = 30


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
    name: str = ""


@dataclass(frozen=True)
class Save:
    # what one document said of itself: its workout's name, or none, and its lifts
    name: str
    lifts: tuple[str, ...]


@dataclass(frozen=True)
class Day:
    day: date
    movements: tuple[Movement, ...]
    saves: tuple[Save, ...] = ()

    @property
    def workouts(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(save.name for save in self.saves if save.name))


def parse_session(text: str, day: date, name: str = "<session>") -> Session:
    movements: list[Movement] = []
    title = ""
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
            # a Markdown document names itself on its first line, above its headings
            if title:
                raise LogError(name, number, "one name line before the first heading")
            title = line
            continue
        sets = _sets(line)
        if sets is None:
            movements[-1] = replace(movements[-1], notes=(*movements[-1].notes, raw))
        elif movements[-1].sets:
            raise LogError(name, number, "a movement has one set line")
        else:
            movements[-1] = replace(movements[-1], sets=sets)
    return Session(day, tuple(movements), title)


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
        shown = sessions[-MOST_DETAILED:]
        blocks = [_detailed(session) for session in shown]
        if len(sessions) > len(shown):
            blocks.append(_earlier(len(sessions) - len(shown)))
        return "\n\n".join(blocks)
    return "\n".join([*(_named(session) for session in sessions), _closing(sessions)])


def _sessions(cora: Host) -> list[Day]:
    by_day: dict[date, tuple[list[Movement], list[Save]]] = {}
    # by name, stably: a day's saves in the order of their moments, and two of one
    # name as they were uploaded
    for document in sorted(cora.documents.all(), key=lambda held: held.name):
        day = _day_of(document.name)
        if day is None:
            continue
        try:
            parsed = parse_session(document.text, day, document.name)
        except LogError as refused:
            cora.show(f"skipped {document.name}", detail=str(refused), failed=True)
            continue
        moved, saves = by_day.setdefault(day, ([], []))
        moved.extend(parsed.movements)
        lifts = tuple(dict.fromkeys(m.name for m in parsed.movements))
        saves.append(Save(parsed.name, lifts))
    return [
        Day(day, tuple(moved), tuple(saves))
        for day, (moved, saves) in sorted(by_day.items())
    ]


def _day_of(name: str) -> date | None:
    dated = DATED.match(name)
    try:
        return date.fromisoformat(dated[1]) if dated else None
    except ValueError:
        return None


def _risen(sessions: list[Day]) -> list[Day]:
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
            # A heading nobody logged a set under is not a session of that exercise, so
            # it is not what the next one is judged against: weighing it would reset the
            # baseline to nothing and mark the session after it risen whatever it did.
            if movement.sets:
                last[movement.name.casefold()] = measure
            marked.append(replace(movement, rose=rose))
        risen.append(replace(session, movements=tuple(marked)))
    return risen


def _only(sessions: list[Day], exercise: str) -> list[Day]:
    wanted = exercise.casefold()
    kept = [
        replace(
            session,
            movements=tuple(
                m for m in session.movements if m.name.casefold() == wanted
            ),
            saves=tuple(
                save
                for save in (
                    replace(
                        save,
                        lifts=tuple(n for n in save.lifts if n.casefold() == wanted),
                    )
                    for save in session.saves
                )
                if save.lifts
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


def _named(session: Day) -> str:
    untitled = [save.lifts for save in session.saves if not save.name]
    parts = [
        *session.workouts,
        *(f"untitled save: {' · '.join(lifts)}" for lifts in untitled),
    ]
    return f"{session.day.isoformat()}: " + " · ".join(parts)


def _earlier(days: int) -> str:
    # The detailed view is every set of every session, and a year of them is a message
    # the model pays for whole. The recent ones answer the usual question, and the rest
    # are a `since` away — said here, so nothing has to be guessed at.
    counted = f"{days} earlier day{'s' if days != 1 else ''}"
    stands = "are" if days != 1 else "is"
    return f"Ask with `since` for what is not here. {counted} {stands} on file."


def _closing(sessions: list[Day]) -> str:
    # what a names view holds beyond the names, said so nothing has to be guessed
    days, saves = len(sessions), sum(len(session.saves) for session in sessions)
    counted = (
        f"{days} day{'s' if days != 1 else ''}, {saves} save{'s' if saves != 1 else ''}"
    )
    return f"{counted}. The sets, reps and weights are in the details."


def _detailed(session: Day) -> str:
    day = session.day.isoformat()
    if session.workouts:
        day += " — " + " · ".join(session.workouts)
    lines = [f"- {_line(movement)}" for movement in session.movements]
    return "\n".join([day, *lines])


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
