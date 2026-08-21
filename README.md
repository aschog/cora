# cora

A "chat with your documents" web app. Ask in your own words and the agent plans
its own steps: it looks things up when a question needs your documents, runs the
domain's tools, remembers what you tell it about yourself between sessions, and
answers directly when none of that is needed. The core is domain-agnostic; domain
specialisation (reference domain: fitness coach) is provided exclusively through
plugins.

- Architecture (start here): [`docs/big-picture.md`](docs/big-picture.md) — the map, the
  nine ports, and what the tests pin down
- One session end to end: [`docs/happy-path.md`](docs/happy-path.md) — upload, question,
  calculation and memory as sequence diagrams, drawn from the live test that walks them
- Development workflow (TDD): [`docs/workflow.md`](docs/workflow.md)
- The docs as a site: `make docs` builds the two pages above plus a reference page for
  every module of `cora.domain`, `cora.ports`, `cora.engine` and `cora.app`, generated
  from the source by `scripts/gen_reference.py`; `make docs-serve` reads it with live
  reload on http://127.0.0.1:8001, beside the app on 8000. Configured in `mkdocs.yml`, and it renders with no network. `make diagram` redraws the
  component map on the big-picture page from `cora.app.assembly`; the SVG is committed, and a
  guard fails when it is behind the source.
- Assignment brief: [`docs/sprints/4/assignment.md`](docs/sprints/4/assignment.md) —
  current sprint; sprint 3's brief, spec and test findings are in `docs/sprints/3/`

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · Chroma · sentence-transformers · Streamlit · React over Starlette —
with ruff, ty and pytest as quality gates. Runtime dependencies are added
feature-by-feature, story by story.

## The packages

The app is the repository root; a `uv` workspace sharing the `cora` namespace. You install
`cora` to use it and add a package to extend it — three kinds of package in all. See
[`docs/big-picture.md`](docs/big-picture.md#the-distributions).

| Package | Ships | Depends on |
|---|---|---|
| `cora` | `cora.domain` · `cora.ports` — the contract<br>`cora.engine` — the agent, the knowledge base, a turn's steps<br>`cora.adapters` — Chroma, OpenRouter, LangGraph, MiniLM<br>`cora.app` — the composition root and its configuration | its technologies, and no user interface |
| `cora-plugin-security` | `cora.plugins.security` — the prompt-injection screen | `cora` |
| `cora-plugin-fitness` | `cora.plugins.fitness` — the reference domain plugin | `cora` |
| `cora-frontend-streamlit` | `cora.frontends.streamlit` — the app you run below | `cora` |
| `cora-frontend-react` | `cora.frontends.react` — the same app over HTTP, drawn by a React page | `cora` |

`cora.plugins.*` and `cora.frontends.*` are the extension points: another domain or a
second user interface is a package to add, not a file to edit. A plugin need not be a
domain — the prompt-injection screen contributes one validation rule and nothing else.

cora carries no plugin and loads none: bare cora is a document-grounded assistant with no
persona and no screen, and `CORA_PLUGINS` is how a deployment adds either.

The tree says which is which by its position:

```
src/cora/                          domain  ports  engine  adapters  app
plugins/fitness  plugins/security  one of many — the directory expects siblings
frontends/streamlit  frontends/react
```

`src/` is the app; a directory beside it is an extension point, named in the plural for
that reason. So `ls` is the shortest description of what can be extended.

The layers inside `src/cora/` are modules, not distributions: nothing in the install stops
`cora.engine` importing Chroma, so `tests/guards/test_architecture.py` walks the imports and
fails the build if it does.

## Setup

```sh
uv sync                                    # install Python 3.12 env + deps
git config core.hooksPath .githooks       # enable pre-commit + commit-msg hooks
```

## Run the app

```sh
export OPENROUTER_API_KEY=sk-or-...        # required (https://openrouter.ai/keys)
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness
make run                                   # or: make run-env, to read the key from .env
```

`make run` wraps `uv run streamlit run` over the app's module path. The target exists so
the command survives the next time a package moves — the path itself is one line, in the
`Makefile`.

The React shell is the same app behind an HTTP surface. `make run-react` builds the page
and then serves it with the API from one process on `127.0.0.1:8000`; in development run
`make run-react` and `make ui` side by side, and Vite serves the page on `5173`, proxying
`/api` to the first. The server reads only the build at `frontends/react/ui/dist`, so
`make ui` is the one that shows a source change as you save it — `make ui-build` is the
same build on its own.

In that shell the answer appears as cora writes it, rather than all at once when the turn
ends; a `[1]` becomes clickable once the turn lands and its citations are resolved. The
Streamlit page waits for the finished turn, as it always did.

cora loads no plugin unless asked, so the second line is what turns this from a bare
document assistant into the coaching app with a prompt-injection screen. Drop it to see
what the box does on its own. `make run-env` reads its environment from `.env` instead,
so put `CORA_PLUGINS` there too rather than exporting it.

Upload a document (txt/md/pdf) in the sidebar, then ask about it — answers cite
the passages they used. Click a `[1]` in an answer and that document opens beside the
chat with the cited passage highlighted; closing it gives the chat its full width back.
The steps appear as cora takes them and stay with the answer under *How I got there*:
what it decided, which tool it ran with which arguments, and what came back. A question
that needs no documents is answered without searching them.

Ask a question the documents can't answer and cora says so rather than filling the gap
from what the model happens to know: with nothing uploaded it asks you for documents,
and with documents that don't cover the question it says that instead. Small talk is
still answered as small talk.

Ask it to remember something — "remember that I train on Tuesdays and Thursdays",
"I'm vegetarian, keep that in mind" — and it keeps that between sessions: the
sidebar's *What I remember* lists every fact it holds, forgets one at a time, or
forgets everything. It only remembers when you ask it to, never on its own judgement,
and each save appears in the trace like any other tool call. The conversation itself
lives as long as the browser session; what is remembered outlives it.

Optional environment overrides: `CORA_MODEL` (default `openai/gpt-4o-mini`; also
accepted as `OPENROUTER_MODEL`, the prefix the key and base URL use),
`CORA_PLUGINS` (comma-separated, in composition order; empty by default — name
`cora.plugins.security` for the prompt-injection screen and `cora.plugins.fitness` for
the coaching domain), `CORA_TOP_K` (default `5`),
`CORA_MAX_TOOL_ROUNDS` (default `8`; one round is a model call plus the tools it
asks for, document search included — and the budget is per question, not per
conversation), `CORA_HISTORY_TURNS` (past messages of the conversation sent with
each question — the default `20` is about ten question-and-answer exchanges, and
`0` sends none), `CORA_DB_PATH` (where Chroma persists; the default `.cora/chroma`
is relative to the working directory), `CORA_MEMORY_PATH` (where remembered facts
persist; the default `.cora/memory.sqlite` sits beside it, and is relative the same
way), `CORA_DOCUMENTS_PATH` (where the text behind each citation persists, so clicking
`[1]` can open the passage; the default `.cora/documents.sqlite` sits beside the others),
`CORA_LOG_PATH` (where the debug trace is written when `CORA_DEBUG` is on; the default
`.cora/logs/cora.log` is relative like the stores beside it), `OPENROUTER_BASE_URL`,
`CORA_DEBUG`. The counts are rejected at
startup if they fall below their lowest useful value — `0` for history turns, `1`
for the others.

Three belong to the React shell alone: `CORA_UI_PATH` (the built page to serve; the
default sits beside the package at `frontends/react/ui/dist`, which a wheel install has
no copy of, so a deployment that serves a build names it here), `CORA_HOST` and
`CORA_PORT` (default `127.0.0.1` and `8000`). With no build at the path it names, the
API still answers and `/` is simply not served — which is a dev machine running the page
on Vite. A setting the shell cannot use is refused before anything is built, as one line
on stderr and a non-zero exit.

Its HTTP surface bounds what it will read, because the cap on a document is applied only
once the whole of it is in memory. `POST /api/documents` answers `413` for an upload past
that cap and `411` for a multipart body that declares no length at all — a ceiling a
client can step around by chunking is not a ceiling. `POST /api/ask` bounds its own body
on the reading instead, so it needs no declared length. That route answers as a
server-sent-event stream: a `step` event per step as it is taken, a `text` event per piece
the model writes as it writes it, an `aside` event when a round it wrote in ended in a
tool call, then one `turn` event carrying the finished turn — which is what a client
keeps. A turn may take several rounds and only the last of them is the answer, so it is
the pieces since the last `aside` that are the same text arriving early; the ones before
it were the model writing its way to a tool call, and a client drops them. Every refusal the
shell models
arrives as `{"error": "<one sentence>"}` under the code and headers it was raised with —
cora's own, the form parser's and Starlette's alike. A failure nobody modelled is still
the server's plain-text 500.

Three more belong to whichever model `CORA_MODEL` names, and are set with it:
`CORA_MAX_OUTPUT_TOKENS` (default `8192`), `CORA_REQUEST_TIMEOUT` (seconds per model
request, default `90`) and `CORA_REASONING_EFFORT` (`low`, `medium` or `high`; default
`low`). A reasoning model such as `openai/gpt-5-mini` bills its thinking to the same
token budget it writes the answer from and takes correspondingly longer to arrive, so a
cap sized for a model that does not reason cuts every long answer off — and raising it
alone only trades that truncation for a timeout. The effort is the dial between them: on
one question `low` answered in 22-25s against `medium`'s 32-61s, citing the documents
either way, while `high` spent an entire 8192-token budget thinking and returned no
answer at all. A model that does not reason ignores the setting rather than refusing it.

Set `CORA_DEBUG` to `1` or `true` to trace what crosses the ports — one truncated
line per embed, retrieval (with sources and scores) and model round trip, printed
to the terminal running Streamlit. Any other value leaves it off, so tracing is
never enabled by accident; the API key never crosses a port.

## Manual testing

With the API key in a local `.env` file (`OPENROUTER_API_KEY=sk-or-...`):

```sh
make run-env
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
make ui-test                  # the React page's own tier (vitest over happy-dom)
make ui-test-browser          # the browser tier (vitest over real Chromium; opt-in)
```

No browser is needed for any *local* gate: the Streamlit UI is driven headlessly through
its `AppTest`, including the live tier, and the React page through `happy-dom`. The React
tier is the one gate that needs node, which is why the pre-commit hook does not run it.

One tier does need a browser, and CI is where it gates: the pre-commit hook leaves it out
and so does `npm test`. Two things are invisible to happy-dom. What the reader keeps while
an answer is being written — a selection inside the paragraph still growing — survives or
collapses identically there, because it moves no selection boundary when a text node is
rewritten. And it applies no stylesheet, so what colour the page actually draws a cited
passage in cannot be read from it at all. `make ui-test-browser` asserts both in Chromium;
locally that needs `npx playwright install chromium --only-shell` once.

The `llm` tier is the only one that spends money. It runs the whole shipped stack —
the composition root, a real Chroma store and embedder, and OpenRouter over the
network — against the assembled page, because a scripted model answers however the
script says and so can never show the real one ignoring an instruction. It needs
`OPENROUTER_API_KEY` (here via `--env-file .env`); without the key it skips with a
reason naming the variable — never a failure, never a silent pass — which is why it
stays out of CI.

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) runs those same gates on every push, plus two tiers the hook leaves
out: the integration tests, and the React page's own.
