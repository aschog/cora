# Get started

Having it running. What cora *is* is the [front door](../index.md).

## Install

Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 — the page is built from
source — and an [OpenRouter key](https://openrouter.ai/keys):

<!-- --8<-- [start:install] -->
```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
```
<!-- --8<-- [end:install] -->

## Load the plugins

A plugin does not have to be installed: drop it in the folder and cora loads it.
- The rest of what the folder does: [load plugins](load-plugins.md).

## Run

<!-- --8<-- [start:run] -->
```sh
export OPENROUTER_API_KEY=sk-or-...
make run                                   # or: make run-env, to read the key from .env
```
<!-- --8<-- [end:run] -->

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000`; `make run-env` reads the environment from `.env` instead.

## Gates

```sh
uv run ptw .      # test watch mode (unit tier, reruns on save)
uv run pytest     # unit tests — the tier the hook runs
uv run ruff format . && uv run ruff check . && uv run ty check
```

The hook runs those on commit and CI on every push; messages follow
[Conventional Commits](https://www.conventionalcommits.org).

```sh
npm --prefix frontends/react/ui run lint    # eslint, plus what it cannot see
npx --prefix frontends/react/ui tsc -b      # type check
npm --prefix frontends/react/ui test        # unit tier, happy-dom
```

CI runs the page's three and the hook does not: they need Node, and a commit touching
no TypeScript should not wait for it.

`make e2e` drives cora through a real browser against a real server, with
`scripts/fake_model_service.py` standing in for the provider — so a run costs nothing
and says the same thing every time. `make e2e-live` runs its one live spec against the
model a deployment answers from, reading the key from `.env`. Local only: they want a
browser, and nothing runs them for you.

## The packages

The repository root is the app: a `uv` workspace sharing the `cora` namespace. Install
`cora` to use it, add a package to extend it — a plugin or a frontend.
[Where the boundary is drawn](../big-picture.md#the-map).
