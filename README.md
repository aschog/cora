# cora

A "chat with your documents" web app. Ask in your own words and the agent plans
its own steps: it looks things up when a question needs your documents, runs the
domain's tools, and answers directly when neither is needed. The core is
domain-agnostic; domain specialisation (reference domain: fitness coach) is
provided exclusively through plugins.

- Architecture (start here): [`docs/big-picture.md`](docs/big-picture.md) — the map, the
  five ports, and what the tests pin down
- Development workflow (TDD): [`docs/workflow.md`](docs/workflow.md)
- Assignment brief: [`docs/sprints/4/assignment.md`](docs/sprints/4/assignment.md) —
  current sprint; sprint 3's brief, spec and test findings are in `docs/sprints/3/`

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · Chroma · sentence-transformers · Streamlit — with ruff, ty and pytest as
quality gates. Runtime dependencies are added feature-by-feature, story by story.

## Setup

```sh
uv sync                                    # install Python 3.12 env + deps
git config core.hooksPath .githooks       # enable pre-commit + commit-msg hooks
```

## Run the app

```sh
export OPENROUTER_API_KEY=sk-or-...        # required (https://openrouter.ai/keys)
uv run streamlit run packages/app/src/cora/app/ui/streamlit_app.py
```

Upload a document (txt/md/pdf) in the sidebar, then ask about it — answers cite
the sources they used. The steps appear as cora takes them and stay with the
answer under *How I got there*: what it decided, which tool it ran with which
arguments, and what came back. A question that needs no documents is answered
without searching them.

Optional environment overrides: `CORA_MODEL` (default `openai/gpt-4o-mini`),
`CORA_PLUGIN` (default `cora.plugins.fitness`), `CORA_TOP_K` (default `5`),
`CORA_RETRIEVAL` (`plain` by default; `advanced` turns on query translation and
self-query filtering — RAG-Fusion — for one extra model call per question;
`hybrid` fuses dense and BM25 keyword rankings with no extra model call),
`CORA_FUSION_QUERIES` (default `4`; sub-queries advanced mode fans out per
question), `CORA_MAX_TOOL_ROUNDS` (default `8`; one round is a model call plus the tools it
asks for, document search included), `CORA_HISTORY_TURNS` (past
messages sent with each question — the default `20` is about ten
question-and-answer exchanges, and `0` switches memory off), `CORA_DB_PATH`
(where Chroma persists; the default `.cora/chroma` is relative to the working
directory), `OPENROUTER_BASE_URL`, `CORA_DEBUG`. The counts are rejected at
startup if they fall below their lowest useful value — `0` for history turns, `1`
for the others — and `CORA_RETRIEVAL` must be `plain`, `advanced`, or `hybrid`.

Set `CORA_DEBUG` to `1` or `true` to trace what crosses the ports — one truncated
line per embed, retrieval (with sources and scores) and model round trip, printed
to the terminal running Streamlit. Any other value leaves it off, so tracing is
never enabled by accident; the API key never crosses a port.

## Manual testing

With the API key in a local `.env` file (`OPENROUTER_API_KEY=sk-or-...`):

```sh
uv run --env-file .env streamlit run packages/app/src/cora/app/ui/streamlit_app.py
```

Sample documents for exercising the upload paths (txt, md, and pdf) live in
`samples/`. Upload each one in the sidebar, then ask questions against them —
e.g. "How much protein should I eat?" or "What are common deadlift mistakes?".

## Development commands

```sh
uv run ptw .                  # test watch mode (unit tier, reruns on save)
uv run pytest                 # unit tests (default; fast, no network/models/UI)
uv run pytest -m integration  # integration tier (real Chroma, embeddings, Streamlit)
uv run --env-file .env pytest -m llm   # live acceptance: real OpenRouter round-trip, costs tokens
uv run ruff format .          # format
uv run ruff check .           # lint
uv run ty check               # type check
```

No browser is needed anywhere: the UI is driven headlessly through Streamlit's
`AppTest`, including the live tier.

The `llm` tier is the only one that spends money. It runs the whole shipped stack —
the composition root, a real Chroma store and embedder, and OpenRouter over the
network — against the assembled page, because a scripted model answers however the
script says and so can never show the real one ignoring an instruction. It needs
`OPENROUTER_API_KEY` (here via `--env-file .env`); without the key it skips with a
reason naming the variable — never a failure, never a silent pass — which is why it
stays out of CI.

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) mirrors the same gates on every push.
