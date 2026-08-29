# CLAUDE.md

What cora is in @README.md stays as a link — open it when relevant.
@docs/workflow.md

## Rules 

- **Workflow** — `docs/workflow.md` is the authoritative process for planning and
  building features. Superpowers process skills (`brainstorming`, etc.) are welcome,
  but they run *inside* that workflow, not instead of it: brainstorming feeds the
  plan, it doesn't replace it.
- **Tooling** — run everything through `uv run`; never call `python`/`pytest` directly.
  Add dependencies with `uv add` / `uv add --dev`; never edit the lockfile or use pip.
- **Docs are not test-backed** — a `.md` file is prose, and prose is held by a person
  reading it.
- **Secrets** — environment variables only; never logged, never committed.
- **Commits** — plain Conventional Commits; no attribution trailers or co-author lines.
- **Answers** — brief by default; expand only when asked.
- **Plans** — planning is spec-driven, through OpenSpec.
