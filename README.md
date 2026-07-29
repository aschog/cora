# cora

A minimal "chat with your documents" web app. The core is
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
`CORA_PLUGIN` (default `cora.plugins.fitness`), `CORA_TOP_K` (default `5`),
`CORA_RETRIEVAL` (`plain` by default; `advanced` turns on query translation and
self-query filtering — RAG-Fusion — for one extra model call per question),
`CORA_FUSION_QUERIES` (default `4`; sub-queries advanced mode fans out per
question), `CORA_MAX_TOOL_ROUNDS` (default `8`), `CORA_HISTORY_TURNS` (past
messages sent with each question — the default `20` is about ten
question-and-answer exchanges, and `0` switches memory off), `CORA_DB_PATH`
(where Chroma persists; the default `.cora/chroma` is relative to the working
directory), `OPENROUTER_BASE_URL`, `CORA_DEBUG`. The counts are rejected at
startup if they fall below their lowest useful value — `0` for history turns, `1`
for the others — and `CORA_RETRIEVAL` must be `plain` or `advanced`.

Set `CORA_DEBUG` to `1` or `true` to trace what crosses the ports — one truncated
line per embed, retrieval (with sources and scores) and model round trip, printed
to the terminal running Streamlit. Any other value leaves it off, so tracing is
never enabled by accident; the API key never crosses a port.

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
uv run pytest -m e2e          # browser tier (chromium drives the real app; stub LLM, no key)
uv run pytest -m llm          # manual acceptance only, never in CI (needs OPENROUTER_API_KEY)
uv run ruff format .          # format
uv run ruff check .           # lint
uv run ty check               # type check
```

The browser tier needs chromium once per machine — a few hundred MB, so it is not
part of `uv sync`:

```sh
uv run playwright install chromium
```

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) mirrors the same gates on every push.
