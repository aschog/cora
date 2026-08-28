# cora

cora is an agent you chat with, and everything it knows and can do arrives as a plugin.
The core runs a turn and screens what comes in; a plugin gives it a field, tools and rules
of its own. With nothing loaded it still answers.

## What it is for

An agent that is good at your subject usually means somebody built an app for that
subject. cora turns that around: the agent is the part that stays, and the subject is the
part you write — a fitness coach, a trip, a lab notebook. It is for people who extend the
tools they already work in, and would rather point an agent at their own field than wait
for someone to ship one for it. That makes the plugin contract the product surface, not
an extension point bolted to the side of one.

## How it works

You ask; cora works out what the question needs. It builds a brief from the plugins that
are loaded, lets the model call the tools they contribute — searching the documents you
uploaded, recalling what you told it before — and answers with citations you can follow
back to the passage they came from. Every decision it made and every tool it called is on
the trace, so a turn is read back rather than guessed at.

A plugin contributes three things, and may bring only one of them:

- **what cora can do** — a tool, named and given a schema, that the model may call
- **what cora is** — instructions heading its section of the brief
- **what cora will not accept** — a rule that refuses an input before any model runs

With none loaded cora still answers: it searches its documents, remembers what it is
told, asks when it cannot tell, and cites what it used.

## Writing your own plugin

A package with one module in it. You declare what it contributes — a name, instructions,
any tools, any rules — and name the module in `CORA_PLUGINS`; a tool is a name, a
description the model reads, a JSON Schema for its arguments and a function to call.
cora imports no plugin of its own, so nothing you write edits the engine, and a plugin
that brings only rules is as legitimate as one that brings only tools. Step by step, with
a worked example: [write a plugin](docs/how-to/write-a-plugin.md).

## Quick start

Python 3.12, [uv](https://docs.astral.sh/uv/), and an
[OpenRouter key](https://openrouter.ai/keys):

```sh
uv sync                                    # install the environment
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
export OPENROUTER_API_KEY=sk-or-...
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness
make run                                   # or: make run-env, to read the key from .env
```

`make run` wraps `uv run streamlit run` over the app's module path. The target exists so
the command survives the next time a package moves — the path itself is one line, in the
`Makefile`. cora loads no plugin unless asked, so the `CORA_PLUGINS` line is what turns
this from a bare cora into the coaching app with a prompt-injection screen.

Walked through, with what to expect at each step:
[`docs/tutorial/first-session.md`](docs/tutorial/first-session.md).

## The docs

`make docs` builds them as a site — [`mkdocs.yml`](mkdocs.yml) configures it, `make
docs-serve` reads it on http://127.0.0.1:8001 with live reload, and it renders with no
network. Sorted by what you came for:

- **Tutorial** — [your first session](docs/tutorial/first-session.md)
- **Understand** — [what it is made of](docs/big-picture.md), the engine and its nine
  ports · [what happens when you ask](docs/happy-path.md), drawn out of the code that
  runs it
- **How-to** — [write a plugin](docs/how-to/write-a-plugin.md) ·
  [run the React shell](docs/how-to/run-the-react-shell.md) ·
  [watch a turn happen](docs/how-to/watch-a-turn.md)
- **Reference** — a page per module of `cora.domain`, `cora.ports`, `cora.engine` and
  `cora.app`, generated from the source by `scripts/gen_reference.py`
- **Process** — [the TDD workflow](docs/workflow.md) this was built with, and the
  [assignment brief](docs/sprints/4/assignment.md) it was built for; sprint 3's brief,
  spec and test findings are in `docs/sprints/3/`

`make diagram` redraws all six — the component map from `cora.app.assembly`, the
domain's classes through pyreverse and graphviz, and the four sequences on the
walkthrough page out of the methods that take them. The SVGs are committed, and a guard
fails when one is behind the source.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · Chroma · sentence-transformers · Streamlit · React over Starlette —
with ruff, ty and pytest as quality gates. Runtime dependencies are added
feature-by-feature, story by story.

## The packages

The app is the repository root; a `uv` workspace sharing the `cora` namespace. You install
`cora` to use it and add a package to extend it — a plugin or a frontend. Where the
boundary is drawn: [`docs/big-picture.md`](docs/big-picture.md#the-map).

## Gates

```sh
uv run ptw .      # test watch mode (unit tier, reruns on save)
uv run pytest     # unit tests — the tier the hook runs
uv run ruff format . && uv run ruff check . && uv run ty check
```

The hook runs those four on commit and CI runs them on every push; commit messages
follow [Conventional Commits](https://www.conventionalcommits.org).
