# CLAUDE.md

RAG chatbot grounded in your uploaded documents, with swappable domain plugins, shipped as
the `cora` package (src layout).

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
- **Plans** — planning happens in the **current sprint's folder only**
  (`docs/sprints/<n>/`), and the artefact is `story-NN.md`: the story followed by a
  **test list** of failing-test-sized items. Match `docs/sprints/4/done/story-01.md`. Design
  rationale does not go in the file — it lives in the conversation, the commit messages
  and the tests. Earlier sprint folders are build history, not planning input.
