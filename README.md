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

- **what cora can do** — a tool, named and given a schema, that the model may call —
  declared, where it reaches outside cora, so what it returns is labelled, and where it
  changes something out there, so the listing says so, no sub-agent is offered it, and a
  call of it waits for you — and able to ask you for what the model could not supply,
  as a card built out of the schema it already declared
- **what cora is** — instructions heading its section of the brief
- **what cora does as a turn runs** — a handler at a named point in it: refusing the
  question, amending the brief, refusing one tool call, wrapping what a tool returned,
  or replacing the answer that is recorded and handed back

With none loaded cora still answers: it searches its documents, remembers what it is
told, asks when it cannot tell, and cites what it used. It changes nothing outside itself
unless a plugin gave it something that does — and then only once you have said yes.

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
the trace says which, and a question that fits both stops the turn to ask. That is
*Chat*, above the conversation. Name one field instead — *+ Plugin* lists the ones this
deployment loaded — and every later turn is answered in it, through a reload and a
reopen: the pin is the thread's own state. A pin is set once, because a
thread that could change field is a thread whose earlier turns mean something else — a
second field is a second conversation. Naming one scope leaves nothing to route between,
which is how a single-field deployment stays one.

Everything cora stops for is one card. A question between two remembered weights, a
call it is about to make that changes something outside itself, a form it needs filled
in — the same prompt, fields and buttons, drawn by one thing on the page that knows
none of those three apart. A field carries the JSON Schema it came from and the page
draws the control that schema describes, so a plugin adds a card the page has never
seen without touching the page: the card is data cora sends, not code anybody shipped.

Cora asks for what it does not have, as one of those. Where a plugin's tool asks for the
arguments it was called without, cora asks for the values an answer turns on and nobody
has written down — the trip, the dates, the budget — naming the fields itself and putting
them as one form rather than a list of questions you answer one at a time. It is cora's
own, so a deployment with no plugin loaded asks this way too. A card whose required
fields are empty cannot be sent — you fill it in, or you leave it — and a box you skipped
is asked for on another card rather than in prose.

A conversation you are finished with is deleted from the list under *SESSIONS*, from the
control at the end of its row — which asks first, and says what is lost and what is not.
Deleting takes both halves of it: the turns you came back through, and the thread they
were answered on — its pin, what the model was told, and any question it stopped on.
One is not deletable without the other, because a record that is gone and a thread that
is not is a conversation listed nowhere and still there. The one you are reading offers
no delete, and neither does one cora is still answering a question in: you leave the
first, and wait for the second.

A fact under *MEMORY* goes the same way: the same control at the end of its row, the same
question first — and forgetting everything is asked about too, because it is the most
destructive thing either rail offers. What a question says is what is lost *and* what is
not: forgetting a fact leaves your documents and your conversations alone, and deleting a
conversation leaves your documents and what cora remembers alone.

A field owns its documents. Each one cora ingests is kept as a Markdown file of its
cleaned text, under a directory named for the field it was uploaded into: `travel` holds
`kyoto-8f21c0a4e9d3.md`, the upload's hash in the name so one filename uploaded twice is
two files rather than one overwritten. The index beside it keeps the embeddings and
where each passage sits in that file, and nothing else: a
passage's words are read back out of the file when it is retrieved, so the text exists
once and a citation opens onto something you can read yourself. A search sees the field
its turn is running in and no other, and the rail lists and uploads into the field it is
set to. `CORA_DOCUMENTS_PATH` moves the root; a second field is a directory under it.

A document you are finished with is deleted from the rail, from the same control the
other two rails carry — and it asks first. That takes both halves of it: its passages
out of the index, and the file its citations opened onto. The rail lists a name and the
stores keep uploads, so deleting a name takes every upload of it in that field, and the
same file in another field is left where it is. Answers already given keep their
citations and say the document is gone when you open one. Upload it again and it is
indexed again, which is the way back from a mistake.

The travel plugin ships its notes as files under
`plugins/travel/src/cora/plugins/travel/corpus/`; upload them in the documents rail,
with `travel` picked as the field, to give it something to answer from.

It also digs. Ask it what to do with three days somewhere and it sends a researcher: a
tool that runs a bounded loop of its own, makes its lookups one at a time, and comes back
with a single report — so the conversation carries the answer while the trace carries the
searching, nested under the call that started it. Run out of rounds and it writes up what
it has and says so, rather than losing it or offering it as the whole story.

It also reaches past its documents. Ask it what the weather will do and it calls a live
forecast service — no key, nothing to configure — and answers from what came back. A
document holds what somebody wrote down once, and this is the part of an answer that has
to be current instead. What a service says is not cora's own words, so it reaches the model
behind the same untrusted-data label a passage carries, and no plugin can take that off.
It earns no `[n]`: a citation opens onto a passage of a file you uploaded, and a
forecast has none, so the answer says it in cora's own prose and the trace is the record
of the call. A service that is down costs the turn that one call — a friendly sentence,
and the conversation intact.

And it plans, rather than describing a plan. Ask for three days somewhere in a month
under a budget and it works out the steps itself: it asks the model what to do on each
day, prices every week the window allows, pairs the cheapest few with a place to stay
for their own dates, and then *checks* what it built — the stay covers every night, the
return matches the check-out, the total is inside the budget, no date is empty, no
outdoor day sits under a forecast that rules it out. A plan that fails a check is
revised and searched again, twice, and then handed over with every rule it could not
satisfy named. Nothing is quietly relaxed: a budget it cannot meet is said plainly, not
raised. The plan is a shape cora holds rather than a paragraph, kept for the
conversation, so *make it cheaper* revises what was verified instead of starting again —
and saving it writes the plan that passed, refusing one that does not match.

It also prices what it plans piece by piece. Give it a route, a budget and a month you
might go rather than a date you have fixed, and it comes back with the three cheapest
fares and the three cheapest places to stay, each priced and dated. Name a trip without saying where
from or when, and it stops and asks you: a card of the search's own fields, dates
as date pickers, and a button that stays shut until the trip is filled in. Nothing
reaches the service until you submit it, and what is priced is what you wrote.

A window is a search rather than a lookup — the service wants a departure date, so cora
tries one candidate a week across the range and keeps the best of all of them, widening
the interval rather than quietly searching less when the range is long. Your budget and
your restrictions go *into* the search, so an option you ruled out is one you never see
rather than one shown with a caveat. This is the one thing in cora that needs a key: set
`CORA_PLUGIN_TRAVEL_SERPAPI_KEY` and the two searches appear, set nothing and they are
never offered — a tool that can only fail is worse than a tool that was never there.
Prices are what the aggregator showed, not a seat held for you, and the answer says so.

You can drive all of that with no account and no network.
`scripts/fake_search_service.py` answers in the same two shapes and makes its prices out
of the dates it is asked about, so a window really does have a cheapest week in it:

```sh
uv run python scripts/fake_search_service.py    # in its own terminal
export CORA_PLUGIN_TRAVEL_SERPAPI_KEY=anything
export CORA_PLUGIN_TRAVEL_SEARCH_URL=http://127.0.0.1:8909/search
```

`CORA_PLUGIN_TRAVEL_SEARCH_URL` is where the searches go, and the real service is where
they go unless you say otherwise — nothing in the plugin branches on it, so what you are
driving is the code that ships.

And it acts, but only when you say so. A tool that declares it changes something outside
cora does not run on the model's word: the turn stops, the page shows the call — what the
tool says it does, and the arguments the model wrote — and nothing happens until you
approve it. Approve and it runs; decline and nothing outside cora has changed, the model
is told plainly, and the turn still answers. Ask travel to save the itinerary you worked
out and that is the shape of it: a card, then a file. A round that proposes two effects
stops twice and settles both before either runs, so picking the turn up never replays one
that already happened, and the trace carries the approval beside the call it authorised.

The gate is cora's own — a step of the core standing on the only path from the model to
its tools, which a plugin can neither switch off nor imitate, because no handler may stop
a turn. It covers what is declared to cora, which is every tool a plugin registered;
what a plugin's *own* code does inside a call is the trust you extend by loading it.

What an effect produces is a file you keep. It lands under `cora-output` — beside cora's
stores rather than in them, because everything in `.cora/` is bookkeeping a deployment may
delete and an itinerary you approved is not. `CORA_OUTPUT_PATH` moves it. A plugin is
handed the location rather than choosing one, and a filename that would climb out of it is
refused, so no plugin writes that check itself.

A plugin does not have to be installed. Drop a single `.py` file into `./.cora/plugins/`
and cora loads it with no packaging at all, named for the file — the folder is read in
name order after the modules `CORA_PLUGINS` names, and `CORA_PLUGINS_PATH` moves it. It
is read relative to where cora was started, and every file in it is code cora runs —
`CORA_DEBUG` logs which folder that was.
`make plugins` prints what loaded: every plugin under where it came from, with its tools,
its instructions and the points in a turn it subscribed to, and anything registered
without a scope marked `system-wide`. `GET /api/plugins` carries the same listing. A
plugin declares which version of the contract it wants, and one cora does not offer is
refused before its `extend` is called.

A plugin keeps what it worked out. What it puts under a name of its own is there on the
next turn of that conversation, rides the same checkpoint the rest of the turn does, and
goes when the conversation is deleted — a plan it is still revising, a count it is
running, a form half filled in. That is a different thing from what cora remembers,
which is about the *user* and outlives every conversation. And its own work is on the
trace: a plugin running a loop of its own says what it just did, in a line cora signs
with the plugin's name, standing under the call it happened inside.

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
- **Understand** — [what it is made of](docs/big-picture.md), the engine and its ten
  ports · [what happens when you ask](docs/happy-path.md), drawn out of the code that
  runs it · [privacy, and what a plugin costs in trust](docs/privacy-and-ethics.md),
  what leaves your machine and what loading someone else's code buys them
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
