# Fix: consecutive citations only counted the first source

## Problem

The model cites several sources back-to-back, e.g. `...balanced diet [3][1][2].`. Only
`[3]` was listed under **Sources**; `[1]` and `[2]` silently vanished.

`cited_numbers` matched each citation with `(?<![\w\]])\[(\d+)\]`. The `\]` in the
negative lookbehind was there to ignore array indexing (`arr[0][1]`), but it also
rejects any citation glued to a preceding `]` — so in a run `[3][1][2]` only the first
bracket survives.

## Acceptance criteria

- A run of consecutive citations rooted on a non-word char counts **every** number:
  `[3][1][2]` → `(3, 1, 2)`.
- Array indexing stays ignored: `list[2]`, `arr[0][1]` → contribute nothing.
- Existing behaviour holds: distinct, in first-appearance order.

## TDD checklist

- [x] **Red** — `cited_numbers("a balanced diet [3][1][2].") == (3, 1, 2)` fails (`(3,)`);
      the `arr[0][1]` guard test still passes.
- [x] **Green** — match a *run* `(?<![\w\]])(?:\[\d+\])+`, then extract every number
      inside it. Lookbehind at the run start keeps `arr[0][1]` out; the `+` sweeps the
      whole run so glued citations all count.
- [x] **Verify** — format, lint, type check, full suite green (416 passed); drove the
      engine end-to-end with a `[3][1][2]` reply and confirmed all three sources list.
