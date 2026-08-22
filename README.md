# cora

cora is an agent you chat with, and plugins give it a scope. It decides for itself what a
turn needs.

A plugin contributes a prompt, tools and rules of its own. The shipped ones are the
reference pair — a fitness coach and a prompt-injection screen — and the coach is a worked
example of a domain.

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
  [add a file format](docs/how-to/add-a-file-format.md) ·
  [swap the technology behind a port](docs/how-to/swap-a-port.md) ·
  [run the React shell](docs/how-to/run-the-react-shell.md) ·
  [run the tests](docs/how-to/run-the-tests.md) ·
  [watch a turn happen](docs/how-to/watch-a-turn.md)
- **Reference** — [configuration](docs/reference/configuration.md) ·
  [the ports](docs/reference/ports.md) · [the components](docs/reference/components.md) ·
  [a turn, step by step](docs/reference/a-turn.md) ·
  [the packages](docs/reference/packages.md) ·
  [the HTTP surface](docs/reference/http-api.md) · and a page per module of
  `cora.domain`, `cora.ports`, `cora.engine` and `cora.app`, generated from the source by
  `scripts/gen_reference.py`
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
`cora` to use it and add a package to extend it — a plugin or a frontend. What each one
ships and where it lives: [`docs/reference/packages.md`](docs/reference/packages.md). Where
the boundary is drawn: [`docs/big-picture.md`](docs/big-picture.md#the-map).

## Gates

```sh
uv run ptw .      # test watch mode (unit tier, reruns on save)
uv run pytest     # unit tests — the tier the hook runs
uv run ruff format . && uv run ruff check . && uv run ty check
```

The hook runs those four on commit and CI runs them on every push; commit messages
follow [Conventional Commits](https://www.conventionalcommits.org). Every tier, what it
costs, which need a browser and which CI adds:
[`docs/how-to/run-the-tests.md`](docs/how-to/run-the-tests.md).
