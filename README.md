# docchat

A minimal NotebookLM-style "chat with your documents" web app. The core is
domain-agnostic RAG with tool calling; domain specialisation (reference domain:
fitness coach) is provided exclusively through plugins.

- Architecture: [`docs/plans/webapp-overview.md`](docs/plans/webapp-overview.md)
- Development workflow (TDD): [`docs/workflow.md`](docs/workflow.md)
- Assignment spec: [`docs/spec.md`](docs/spec.md)

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

## Development commands

```sh
uv run ptw .                  # test watch mode (unit tier, reruns on save)
uv run pytest                 # unit tests (default tier)
uv run pytest -m integration  # integration tier (real Chroma/embeddings)
uv run pytest -m llm          # manual acceptance (needs OPENROUTER_API_KEY)
uv run ruff format .          # format
uv run ruff check .           # lint
uv run ty check               # type check
```

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) mirrors the same gates on every push.
