## Context

See `proposal.md` — Why. The seam exists: `tests/guards/test_tagline.py` holds five copies
of one sentence to `README.md`'s opening paragraph, and `tests/guards/test_docs.py` holds
every path the docs claim. What is missing is a guard over the *shape* of the first screen
— which is why the reviewer's finding could be true while the suite was green.

## Decisions

- **The guard reads structure, not prose** — sections present, absences shaped, links
  present. Asserting phrases would put a second copy of the README in a test file, and it
  would fail on the rewrite it should allow.
- **An absence is a bullet whose bold lead-in is the thing and whose remainder, after an em
  dash, is the reason.** That is the shape the criterion asks for and the shape a guard can
  check: a bold lead-in with nothing after the dash is a bare absence and fails.
- **"Near the top" is "above the quick start."** An existing heading is the landmark; a
  line count breaks on a rewrap.
- **The showcase link is checked by host**, not by URL — the entry does not exist yet, so
  the chore swaps the link and the guard is never edited.
- **`test_tagline.py` is not touched.** The sentence changing is what exercises it.
- New guard at `tests/guards/test_front_door.py`. No port and no generated diagram is
  touched; blast radius is in `proposal.md`.

## Risks / Trade-offs

- **A structural guard cannot prove a reader understood** → it holds the parts in place;
  whether they convey the idea is the Phase 4 read against the criterion.
- **The sentence goes in before the code that widens it** — stories 4 to 7 are what make
  "everything it knows and can do arrives as a plugin" fully true → it is accurate about
  today's contract, and the alternative is writing the README last, which is the finding.
