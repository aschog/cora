## Context

See proposal.md — Why. The site was three things behind one `make docs`: written pages,
a reference generated from docstrings, and guards that read both.

## Goals / Non-Goals

- Goal: one file a reader holds, with nothing between them and the commands.
- Goal: every generated artefact that has a life of its own outlives the site.
- Non-Goal: changing what any public name promises, or the docstring policy behind it.
- Non-Goal: keeping a published surface of any kind — nothing replaces the site.

## Decisions

- The written pages go rather than moving into `README.md` whole: a front door that
  absorbed fifteen pages is the 348-line README this project already deleted once.
- Only the commands come back, because a command is the one thing a reader cannot
  derive from the tree, and the tree is what the rest of the pages described.
- The generated diagrams stay: `scripts/gen_*_map.py` write to `docs/assets/`, and
  `tests/guards/test_diagrams.py` reads each SVG for what it contains, so the guard that
  catches a port or a step added without a redraw is independent of any site.
- `tests/guards/test_docs.py` goes, because it swept a tree of pages that no longer
  exists, but the front door keeps a guard of its own: a README linking a deleted page is
  the failure this change was made by, and it is the one thing reading cannot catch.
- `docs/workflow.md` stays where it is — `CLAUDE.md` loads it as the process, and it was
  never a page of the site.
- Sprint history is pruned to the four files `docs/workflow.md` names a sprint folder
  holds, so the rule is the project's own rather than one invented here; what goes is
  superseded by the 67 changes under `openspec/changes/archive/`.

## Risks / Trade-offs

- A reader's bookmark into `docs/` breaks → the README carries what they were after, and
  git holds every deleted page.
- The docstring policy loses the reference that justified it → the rule is unchanged and
  the justification is repointed, because another author still writes against those four
  layers.
- Sprint 3's plans predate OpenSpec, so the archive does not cover them → they are build
  history rather than product, and main's git history keeps them reachable.

## Migration Plan

Deletion, then `README.md`, then the pointers that named a deleted page — `openspec/config.yaml`
and the docstring passage in `docs/workflow.md`. Rollback is `git revert` of the three
commits; nothing here is stateful.
