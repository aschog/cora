"""The sequences of `sequences.py` drawn as UML, in the hand the other two maps use.

A sequence diagram places itself: lifelines stand as far apart as the widest thing said
between them, a fragment is a box around the lines it holds, and an execution bar runs
from the message that started one to the message that answered it.
"""

from dataclasses import dataclass
from pathlib import Path

from sequences import (
    ROOT,
    Fragment,
    Line,
    Reply,
    Sequence,
    round_taken,
    search,
    turn,
    upload,
)

STYLE = """
  <style>
    text { font: 13px/1.4 -apple-system, "Segoe UI", Roboto, sans-serif; fill: #202124 }
    .role { font-weight: 600 }
    .kind { font-size: 11.5px; fill: #5f6368 }
    .head { fill: #f2f8fd; stroke: #2b7fc4; stroke-width: 1.4 }
    .life { stroke: #9aa0a6; stroke-width: 1.1; stroke-dasharray: 5 5 }
    .bar { fill: #ffffff; stroke: #2b7fc4; stroke-width: 1.1 }
    .send { stroke: #202124; stroke-width: 1.3; fill: none; marker-end: url(#sent) }
    .back { stroke: #6b7280; stroke-width: 1.1; fill: none;
            stroke-dasharray: 6 4; marker-end: url(#answered) }
    .said { font-size: 12.5px }
    .sheet { fill: #f8f9fa; stroke: none }
    .answer { font-size: 11.5px; fill: #6b7280; font-style: italic }
    .frame { fill: none; stroke: #9aa0a6; stroke-width: 1.1 }
    .tab { fill: #f8f9fa; stroke: #9aa0a6; stroke-width: 1.1 }
    .operator { font-size: 11px; font-weight: 600; fill: #5f6368;
                letter-spacing: .03em }
    .guard { font-size: 11.5px; fill: #14425f; font-style: italic }
    .split { stroke: #9aa0a6; stroke-width: 1; stroke-dasharray: 4 4; fill: none }
    @media (prefers-color-scheme: dark) {
      text { fill: #e8eaed }
      .kind { fill: #9aa0a6 }
      .head { fill: #10283a; stroke: #6fb6ea }
      .bar { fill: #303134; stroke: #6fb6ea }
      .send { stroke: #e8eaed }
      .sheet { fill: #2b2c2f }
      .back { stroke: #bdc1c6 }
      .answer { fill: #bdc1c6 }
      .frame, .split { stroke: #bdc1c6 }
      .tab { fill: #2b2c2f; stroke: #bdc1c6 }
      .operator { fill: #bdc1c6 }
      .guard { fill: #cfe6f7 }
    }
  </style>
"""

MARGIN = 24.0
HEAD_H = 46.0
HEAD_GAP = 30.0
ROW = 34.0
SELF_ROW = 46.0
TAB_H = 19.0
GUARD_H = 22.0
FRAME_TOP = 6.0
FRAME_END = 8.0
BAND_GAP = 4.0
# Room under a fragment before the next message, so its label is read as being outside
# the box rather than sitting on its edge.
AFTER_FRAME = 20.0
BAR_W = 10.0
STUB = 14.0
INSET = 9.0
LOOP_W = 26.0


def _wide(text: str, size: float = 12.5, bold: bool = False) -> float:
    per = 0.58 if bold else 0.54
    return len(text) * size * per


@dataclass(frozen=True)
class Sent:
    """One message, placed: which columns it runs between, and how high up."""

    frm: int
    to: int
    y: float
    label: str
    answer: bool


@dataclass(frozen=True)
class Frame:
    """A combined fragment, placed: its box, and where each operand's guard sits."""

    top: float
    bottom: float
    depth: int
    operator: str
    bands: tuple[tuple[str, float], ...]


def _head_widths(sequence: Sequence) -> list[float]:
    return [
        max(_wide(line.role, 13, bold=True), _wide(f": {line.kind}", 11.5)) + 36
        for line in sequence.lifelines
    ]


def _placed(sequence: Sequence) -> tuple[list[Sent], list[Frame], float]:
    column = {line.role: index for index, line in enumerate(sequence.lifelines)}
    sent: list[Sent] = []
    frames: list[Frame] = []

    def place(lines: tuple[Line, ...], y: float, depth: int) -> float:
        for line in lines:
            if isinstance(line, Fragment):
                top = y
                y += TAB_H + FRAME_TOP
                bands: list[tuple[str, float]] = []
                for guard, inner in line.operands:
                    bands.append((guard, y))
                    y += GUARD_H
                    y = place(inner, y, depth + 1)
                    y += BAND_GAP
                frames.append(
                    Frame(top, y + FRAME_END, depth, line.operator, tuple(bands))
                )
                y += FRAME_END + AFTER_FRAME
                continue
            frm, to = column[line.sender], column[line.receiver]
            sent.append(Sent(frm, to, y, line.label, isinstance(line, Reply)))
            y += SELF_ROW if frm == to else ROW
        return y

    bottom = place(sequence.lines, MARGIN + HEAD_H + 34, 0)
    return sent, frames, bottom + 10


def _centres(sequence: Sequence, sent: list[Sent]) -> list[float]:
    heads = _head_widths(sequence)
    half = [width / 2 for width in heads]
    gaps = [half[index] + half[index + 1] + HEAD_GAP for index in range(len(heads) - 1)]
    for message in sent:
        left, right = sorted((message.frm, message.to))
        room = _wide(message.label) + 34
        if left == right:
            if left < len(gaps):
                gaps[left] = max(gaps[left], LOOP_W + room)
            continue
        share = room / (right - left)
        for index in range(left, right):
            gaps[index] = max(gaps[index], share)
    centres = [MARGIN + half[0]]
    for index, gap in enumerate(gaps):
        centres.append(centres[index] + gap)
    return centres


def _overhang(sequence: Sequence, sent: list[Sent]) -> float:
    last = len(sequence.lifelines) - 1
    loops = [one for one in sent if one.frm == one.to == last]
    if not loops:
        return 0.0
    return LOOP_W + 10 + max(_wide(one.label) for one in loops)


def _bars(sent: list[Sent]) -> list[tuple[int, float, float]]:
    open_: list[Sent] = []
    bars: list[tuple[int, float, float]] = []
    for message in sent:
        if not message.answer:
            open_.append(message)
            continue
        for index in reversed(range(len(open_))):
            # Both ends have to match: a reply answers the call it came in on, and an
            # object that called itself in between is not the one being answered.
            if open_[index].to == message.frm and open_[index].frm == message.to:
                bars.append((message.frm, open_[index].y, message.y))
                del open_[index]
                break
    return bars + [(one.to, one.y, one.y + STUB) for one in open_]


def _text(x: float, y: float, value: str, style: str, anchor: str = "middle") -> str:
    return (
        f'  <text x="{x:g}" y="{y:g}" class="{style}" text-anchor="{anchor}">'
        f"{_escaped(value)}</text>"
    )


def _escaped(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rect(x: float, y: float, w: float, h: float, style: str, radius: float = 3) -> str:
    return (
        f'  <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}"'
        f' rx="{radius:g}" class="{style}"/>'
    )


def _path(points: list[tuple[float, float]], style: str) -> str:
    head, *rest = points
    drawn = f"M {head[0]:g} {head[1]:g} " + " ".join(f"L {x:g} {y:g}" for x, y in rest)
    return f'  <path d="{drawn}" class="{style}"/>'


MARKERS = (
    "  <defs>"
    '<marker id="sent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8"'
    ' markerHeight="8" orient="auto-start-reverse">'
    '<path d="M 0 1 L 9 5 L 0 9 z" fill="context-stroke"/></marker>'
    '<marker id="answered" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9"'
    ' markerHeight="9" orient="auto-start-reverse">'
    '<path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="context-stroke"'
    ' stroke-width="1.4"/></marker></defs>'
)


def draw(sequence: Sequence) -> str:
    """One sequence as UML draws one: lifelines, messages, and a frame per fragment.

    Raises:
        SystemExit: The sequence has no participants, so there is nothing to draw and
            no drawing to commit.
    """
    if not sequence.lifelines:
        raise SystemExit(
            f"the {sequence.name} sequence met no participants: the method it is read "
            "from sends no message the drawing may show"
        )
    sent, frames, bottom = _placed(sequence)
    centres = _centres(sequence, sent)
    heads = _head_widths(sequence)
    width = centres[-1] + max(heads[-1] / 2, _overhang(sequence, sent)) + MARGIN
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {bottom:g}"'
        f' width="{width:g}" height="{bottom:g}" role="img"'
        f' aria-label="{_escaped(_caption(sequence, sent))}">',
        STYLE.strip("\n"),
        MARKERS,
    ]
    for frame in frames:
        out += _frame(frame, width)
    for index, line in enumerate(sequence.lifelines):
        centre, span = centres[index], heads[index]
        out.append(_rect(centre - span / 2, MARGIN, span, HEAD_H, "head"))
        out.append(_text(centre, MARGIN + 20, line.role, "role"))
        if line.kind:
            out.append(_text(centre, MARGIN + 36, f": {line.kind}", "kind"))
        out.append(_path([(centre, MARGIN + HEAD_H), (centre, bottom - 10)], "life"))
    for column, top, end in _bars(sent):
        out.append(_rect(centres[column] - BAR_W / 2, top, BAR_W, end - top, "bar", 1))
    for message in sent:
        out += _message(message, centres)
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _message(message: Sent, centres: list[float]) -> list[str]:
    style = "back" if message.answer else "send"
    said = "answer" if message.answer else "said"
    frm, to = centres[message.frm], centres[message.to]
    if message.frm == message.to:
        turn = frm + BAR_W / 2
        return [
            _path(
                [
                    (turn, message.y),
                    (turn + LOOP_W, message.y),
                    (turn + LOOP_W, message.y + 18),
                    (turn + BAR_W / 2, message.y + 18),
                ],
                style,
            ),
            _text(turn + LOOP_W + 10, message.y + 5, message.label, said, "start"),
        ]
    step = BAR_W / 2 if to > frm else -BAR_W / 2
    middle = (frm + to) / 2
    span = _wide(message.label)
    crossed = [
        centre
        for index, centre in enumerate(centres)
        if min(message.frm, message.to) < index < max(message.frm, message.to)
        and middle - span / 2 - 4 <= centre <= middle + span / 2 + 4
    ]
    # A label long enough to reach past the lifelines it flies over is read on top of
    # them, so it is given ground of its own — the alternative is a dashed line struck
    # through the middle of a word. Only where it happens: a chip behind every label
    # would be a box around text nothing runs through.
    ground = (
        [_rect(middle - span / 2 - 5, message.y - 19, span + 10, 16, "sheet", 2)]
        if crossed
        else []
    )
    return [
        _path([(frm + step, message.y), (to - step, message.y)], style),
        *ground,
        _text(middle, message.y - 7, message.label, said),
    ]


def _frame(frame: Frame, width: float) -> list[str]:
    left = MARGIN / 2 + frame.depth * INSET
    right = width - MARGIN / 2 - frame.depth * INSET
    tab = _wide(frame.operator, 11, bold=True) + 22
    out = [
        _rect(left, frame.top, right - left, frame.bottom - frame.top, "frame", 2),
        _rect(left, frame.top, tab, TAB_H, "tab", 2),
        _text(left + 10, frame.top + 14, frame.operator, "operator", "start"),
    ]
    for index, (guard, y) in enumerate(frame.bands):
        if index:
            out.append(_path([(left, y - 6), (right, y - 6)], "split"))
        out.append(_text(left + tab + 12, y + 8, f"[{guard}]", "guard", "start"))
    return out


def _caption(sequence: Sequence, sent: list[Sent]) -> str:
    taking = ", ".join(line.label for line in sequence.lifelines)
    calls = sum(1 for one in sent if not one.answer)
    return (
        f"A UML sequence diagram of {sequence.name}: {calls} messages between "
        f"{taking}. Generated by scripts/gen_session_maps.py."
    )


ASSETS = ROOT / "docs" / "assets"
DRAWINGS = {
    "upload-map.svg": upload,
    "turn-map.svg": turn,
    "round-map.svg": round_taken,
    "search-map.svg": search,
}


def written() -> dict[Path, str]:
    return {ASSETS / name: draw(read_it()) for name, read_it in DRAWINGS.items()}


if __name__ == "__main__":
    for path, drawing in written().items():
        path.write_text(drawing)
        print(f"wrote {path.relative_to(ROOT)}")
