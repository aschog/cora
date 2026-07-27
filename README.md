# cora

A minimal NotebookLM-style "chat with your documents" web app. The core is
domain-agnostic RAG with tool calling; domain specialisation (reference domain:
fitness coach) is provided exclusively through plugins.

- Architecture: [`docs/plans/webapp-overview.md`](docs/plans/webapp-overview.md)
- Development workflow (TDD): [`docs/workflow.md`](docs/workflow.md)
- Assignment spec: [`docs/spec.md`](docs/spec.md) (original brief: [`docs/assignment.md`](docs/assignment.md))

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangChain over OpenRouter ·
Chroma · sentence-transformers · Streamlit — with ruff, ty and pytest as
quality gates. Runtime dependencies are added feature-by-feature; see the
roadmap in the architecture plan.

## Setup

```sh
uv sync                                    # install Python 3.12 env + deps
git config core.hooksPath .githooks       # enable pre-commit + commit-msg hooks
```

## Run the app

```sh
export OPENROUTER_API_KEY=sk-or-...        # required (https://openrouter.ai/keys)
uv run streamlit run src/cora/app/ui/streamlit_app.py
```

Upload a document (txt/md/pdf) in the sidebar, then ask about it — answers cite
their sources, and any tool runs appear under the answer.

Optional environment overrides: `CORA_MODEL` (default `openai/gpt-4o-mini`),
`CORA_PLUGIN` (default `cora.plugins.fitness`), `CORA_TOP_K`,
`CORA_MAX_TOOL_ROUNDS`, `CORA_HISTORY_TURNS` (past turns sent with each
question; `0` switches memory off), `OPENROUTER_BASE_URL`.

## Manual testing

With the API key in a local `.env` file (`OPENROUTER_API_KEY=sk-or-...`):

```sh
uv run --env-file .env streamlit run src/cora/app/ui/streamlit_app.py
```

Sample documents for exercising the upload paths (txt, md, and pdf) live in
`samples/`. Upload each one in the sidebar, then ask questions against them —
e.g. "How much protein should I eat?" or "What are common deadlift mistakes?".

## Development commands

```sh
uv run ptw .                  # test watch mode (unit tier, reruns on save)
uv run pytest                 # unit tests (default; fast, no network/models/UI)
uv run pytest -m integration  # integration tier (real Chroma, embeddings, Streamlit)
uv run pytest -m llm          # manual acceptance only, never in CI (needs OPENROUTER_API_KEY)
uv run ruff format .          # format
uv run ruff check .           # lint
uv run ty check               # type check
```

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) mirrors the same gates on every push.
