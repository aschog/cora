# CLAUDE.md

cora is an agent you chat with, and everything it knows and can do arrives as a plugin.
Shipped as the `cora` package (src layout). That sentence is `README.md`'s opening, and a
guard keeps every copy of it in step — so edit it there.

@docs/workflow.md

`README.md` (setup, gates, test tiers, watch mode) stays as a link — open it when
relevant.

## Rules (not covered by the imports above)

- **Workflow** — `docs/workflow.md` is the authoritative process for planning and
  building features. Superpowers process skills (`brainstorming`, etc.) are welcome,
  but they run *inside* that workflow, not instead of it: brainstorming feeds the
  plan, it doesn't replace it.
- **Tooling** — run everything through `uv run`; never call `python`/`pytest` directly.
  Add dependencies with `uv add` / `uv add --dev`; never edit the lockfile or use pip.
- **Secrets** — environment variables only; never logged, never committed.
- **Commits** — plain Conventional Commits; no attribution trailers or co-author lines.
- **Answers** — brief by default; expand only when asked.
- **Plans** — planning is spec-driven, through OpenSpec. A story becomes a change under
  `openspec/changes/`: the story and its criteria as a delta on `openspec/specs/`, the
  architecture in `design.md`, why / what changes / impact in `proposal.md`, and a **test
  list** in `tasks.md` where every item is one failing test. `openspec/config.yaml` holds
  the rules the `/opsx:` commands must follow, so edit it there rather than restating them.
  The
  sprint folder (`docs/sprints/<n>/`) keeps the brief, the story cut and the feedback
  backlog; `openspec/specs/` says what cora does today and is always in scope. Earlier
  sprint folders — and `docs/sprints/4/done/`, which holds the `story-NN.md` files this
  replaces — are build history, not planning input.
