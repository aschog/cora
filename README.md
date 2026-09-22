# cora

![CoRa: one core, endless plugin power](docs/assets/hero.png)

On the showcase: [cora](https://showcase.turingcollege.com/project/d74b5ac2-789f-485c-ad57-d118f8d4602b).

## Why

An agent that is good at your subject usually means somebody built an app for that
subject. Cora turns that around: the agent is the part that stays, and the subject is
the part you build yourself — a fitness coach, a trip, a lab notebook.

## With nothing loaded

It still answers: it searches its documents, remembers what it is told, asks when it
cannot tell, and cites what it used. It changes nothing outside itself unless a plugin
gave it something that does.

## A field can bring a screen

A plugin may hand cora a page of its own, and cora serves it at its field's address. The
fitness plugin brings one: a kettlebell trainer that logs the workout you just did into
the field, where the coach can answer from it. Pin the field and it fills the screen,
with the conversation beside it.

## One cora, many subjects

A plugin's things live in a field of its own. One SQLite file holds cora's own
bookkeeping and partitions a field's vectors apart from every other field's,
`.cora/documents` is a directory per field holding one Markdown file per upload, and
`.cora/fields` is a directory per field holding the files that field's plugin keeps. A
second subject is a second directory, not a second store. That is the whole layout.

## Start here

```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
```

Symlink the plugins you want into `.cora/plugins`, then run it:

```sh
mkdir -p .cora/plugins
for each in security fitness interview travel vocab; do
  ln -s "$(pwd)"/plugins/$each/src/cora/plugins/$each .cora/plugins/$each
done

export OPENROUTER_API_KEY=sk-or-...
make run                                   # or: make run-env, to read the key from .env
```

`make run` builds the page and serves it with the API from one process on
127.0.0.1:8000. `make bot` runs the Telegram bot instead.

The gates, which the pre-commit hook and CI both run:

```sh
uv run pytest
uv run ruff format . && uv run ruff check . && uv run ty check
npm --prefix frontends/react/ui run lint && npm --prefix frontends/react/ui test
```

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · SQLite with sqlite-vec · sentence-transformers · React over Starlette,
and a Telegram bot beside it.
Gates: ruff, ty and pytest on the Python, eslint, tsc and vitest on the page, and a
browser tier nothing runs for you.
