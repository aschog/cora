# Your first session

Half an hour, one document, and a model you pay for by the token. By the end you will
have uploaded a document, had it answered from, followed a citation back to the passage
it came from, and asked cora to remember something about you.

You need Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 — the page is built
from source, and neither the build nor its dependencies are committed — and an
[OpenRouter key](https://openrouter.ai/keys).

## 1. Install

```sh
uv sync
npm ci --prefix frontends/react/ui
```

## 2. Start it with plugins

```sh
export OPENROUTER_API_KEY=sk-or-...        # required (https://openrouter.ai/keys)
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness
export CORA_SCOPES=fitness
make run                                   # or: make run-env, to read the key from .env
```

cora loads no plugin unless asked, so the second line is what turns this from a bare
cora into the coaching app with a prompt-injection screen. Drop it to see
what the box does on its own. `CORA_SCOPES=fitness` is what says a turn runs as the
coach: the persona and the calculators are that scope's, and the medical filter holds
either way. `make run-env` reads its environment from `.env` instead, so put both there
rather than exporting them.

## 3. Ask it something

Upload a document (txt/md/pdf) in the documents rail on the left, then ask about it —
answers cite the passages they used. Click a `[1]` in an answer and that document opens
with the cited passage highlighted. The steps appear as cora takes them, under the
*STEPS* tab on the right: what it decided, which tool it ran and what came back. A
question that needs no documents is answered without searching them.

Ask it to remember something — "remember that I train on Tuesdays and Thursdays",
"I'm vegetarian, keep that in mind" — and it keeps that between sessions: the *MEMORY*
tab lists every fact it holds, forgets one at a time, or forgets everything. It only remembers when you ask it to, never on its own judgement,
and each save appears in the trace.

## Where to go next

- [What happens when you ask](../happy-path.md) — the same session as sequence diagrams,
  read out of the code that runs it
- [What it is made of](../big-picture.md) — why cora is built this way
- [Write a plugin](../how-to/write-a-plugin.md) — your own domain instead of the coach
