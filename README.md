# cora

<!-- --8<-- [start:what-cora-is] -->
cora is an agent you chat with, and everything it knows and can do arrives as a plugin.
The core runs a turn and screens what comes in; a plugin gives it a field, tools and a
hand in the turn itself. With nothing loaded it still answers.
<!-- --8<-- [end:what-cora-is] -->

On the showcase: [showcase.turingcollege.com](https://showcase.turingcollege.com/).

## What it is for

An agent that is good at your subject usually means somebody built an app for that
subject. cora turns that around: the agent is the part that stays, and the subject is the
part you write — a fitness coach, a trip, a lab notebook. It is for people who extend the
tools they already work in, and would rather point an agent at their own field than wait
for someone to ship one for it.

## How it works

You ask; cora works out what the question needs. It builds a brief from the plugins that
are loaded, lets the model call the tools they contribute — searching the documents you
uploaded, recalling what you told it before — and answers with citations you can follow
back to the passage they came from. Every decision it made and every tool it called is on
the trace, so a turn is read back rather than guessed at.

A plugin contributes three things, and may bring only one of them:

- **what cora can do** — a tool, named and given a schema, that the model may call
- **what cora is** — instructions heading its section of the brief
- **what cora does as a turn runs** — a handler at a named point in it: refusing the
  question, amending the brief, refusing one tool call, wrapping what a tool returned

With none loaded cora still answers: it searches its documents, remembers what it is
told, asks when it cannot tell, and cites what it used.

## Writing your own plugin

Step by step, with a worked example: [write a plugin](docs/how-to/write-a-plugin.md).

## Quick start

Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 — the page is built from
source — and an [OpenRouter key](https://openrouter.ai/keys):

```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
export OPENROUTER_API_KEY=sk-or-...
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness,cora.plugins.travel
export CORA_SCOPES=fitness,travel
make run                                   # or: make run-env, to read the key from .env
```

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000`. The target exists so the command survives the next time a package
moves — the module it names is one line, in the `Makefile`. `make run-env` is the same
thing reading its environment from `.env`, so the exports above go in that file
instead. cora loads no plugin unless asked, so the `CORA_PLUGINS` line is what turns
this from a bare cora into the coaching app with a prompt-injection screen. `CORA_SCOPES`
says which fields a turn *may* run in: the coaching persona and its calculators are the
fitness scope's, the travel persona and its notes are travel's, while the medical filter
and the injection screen are system-wide and hold whatever a turn is running as.

With two fields named, cora reads each question and answers it in the one it belongs to —
the trace says which, and a question that fits both stops the turn to ask. Pin the
conversation to a field in the header and every later turn is answered in it, through a
reload and a reopen: the pin is the thread's own state. A pin is set once, because a
thread that could change field is a thread whose earlier turns mean something else — a
second field is a second conversation. Naming one scope leaves nothing to route between,
which is how a single-field deployment stays one.

A field owns its documents. Each one cora ingests is kept as a Markdown file of its
cleaned text, under a directory named for the field it was uploaded into: `travel` holds
`kyoto-8f21c0a4e9d3.md`, the upload's hash in the name so one filename uploaded twice is
two files rather than one overwritten. The index beside it keeps the embeddings and
where each passage sits in that file, and nothing else: a
passage's words are read back out of the file when it is retrieved, so the text exists
once and a citation opens onto something you can read yourself. A search sees the field
its turn is running in and no other, and the rail lists and uploads into the field it is
set to. `CORA_DOCUMENTS_PATH` moves the root; a second field is a directory under it.

The travel plugin ships its notes as files under
`plugins/travel/src/cora/plugins/travel/corpus/`; upload them in the documents rail,
with `travel` picked as the field, to give it something to answer from.

A plugin does not have to be installed. Drop a single `.py` file into `./.cora/plugins/`
and cora loads it with no packaging at all, named for the file — the folder is read in
name order after the modules `CORA_PLUGINS` names, and `CORA_PLUGINS_PATH` moves it. It
is read relative to where cora was started, and every file in it is code cora runs —
`CORA_DEBUG` logs which folder that was.
`make plugins` prints what loaded: every plugin under where it came from, with its tools,
its instructions and the points in a turn it subscribed to, and anything registered
without a scope marked `system-wide`. The same listing is behind the plug icon on the
page. A plugin declares which version of the contract it wants, and one cora does not
offer is refused before its `extend` is called.

A plugin reads its own settings from the environment, under its own name:
`CORA_PLUGIN_FITNESS_UNITS=imperial` reaches `cora.plugins.fitness` as `units`. Cora's
own `CORA_` variables are a separate namespace, so no plugin can read them.

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
OpenRouter · Chroma · sentence-transformers · React over Starlette —
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
