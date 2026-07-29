# CLAUDE.md

RAG chatbot grounded in your uploaded documents, with swappable domain plugins, shipped as
the `cora` package (src layout).

@docs/workflow.md
@docs/big-picture.md

`docs/plans/webapp-overview.md` (design rationale) and `README.md` (setup, gates, test
tiers, watch mode) stay as links — open them when relevant.

## Rules (not covered by the imports above)

- **Tooling** — run everything through `uv run`; never call `python`/`pytest` directly.
  Add dependencies with `uv add` / `uv add --dev`; never edit the lockfile or use pip.
- **Secrets** — environment variables only; never logged, never committed.
- **Commits** — plain Conventional Commits; no attribution trailers or co-author lines.
- **Answers** — brief by default; expand only when asked.
