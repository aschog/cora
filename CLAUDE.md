# CLAUDE.md

NotebookLM-style RAG chatbot with domain plugins. Distribution `cora` (src
layout) ships a single import package `cora`, layered as: `cora.core`
(domain-agnostic center — `ports`, `services`, plus root value objects &
`errors`), `cora.adapters` (framework edge), `cora.plugins` (domains), and
`cora.app` (composition root, config, UI shell).
Read `docs/big-picture.md` (one-page orientation: layers, components, ports),
`docs/plans/webapp-overview.md` (architecture rationale) and @docs/workflow.md
(TDD workflow) before making changes. Setup and all development commands
(gates, test tiers, watch mode) live in `README.md`.

## Tooling rules

- Always run tools through `uv run`; never call `python`/`pytest` directly.
- Add dependencies with `uv add` (runtime) or `uv add --dev` (tooling) —
  never edit the lockfile or use pip.

## Architecture rules

- **Ports & Adapters.** Business logic lives in pure-Python core modules with
  no framework imports. Ports (chat model, retriever, embedder) are narrow
  interfaces owned by the core.
- **Dependency rule:** UI → Core ← Plugins. The core imports neither the UI nor
  any plugin. LangChain appears in exactly one adapter; same for Chroma,
  sentence-transformers, and Streamlit (thin shell, widgets only). Enforced by
  `tests/cora/test_architecture.py`: `cora.core` may import none of those
  frameworks, nor `cora.adapters`/`cora.plugins`/`cora.app`.
- **Plugins are data, not behaviour:** system prompt, tool definitions
  (pure functions + schema), validation rules, optional seed docs. Adding a
  domain must require zero core changes.
- **Errors:** one small exception hierarchy; every failure maps to a typed
  error with a user-presentable message. Tool failures are data returned to
  the LLM, never crashes. No stack traces to users.
- **Secrets** only via environment variables; never logged, never committed.

## Workflow rules

- Strict TDD (`docs/workflow.md`): red → green → refactor; commit every green
  step. Never write production code without a failing test first.
- Each feature lives on its own branch with a checklist in `docs/plans/<feature>.md`;
  tick items as they land and keep the checklist honest (it is a living document).
- Unit tests use in-memory fakes for the three ports; no network, no model
  downloads, no UI in the default tier.
- Commit messages: plain Conventional Commits — no attribution trailers or
  co-author lines.
- Keep answers brief by default; expand only when asked.
