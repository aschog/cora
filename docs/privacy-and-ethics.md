# Privacy, and what a plugin costs in trust

Two costs, on one page. Uploading your documents to cora sends some of them to a model
provider and keeps the rest on your disk. Loading somebody else's plugin runs their code
with your permissions. Neither is hidden and neither is free, so here is what each one
actually is.

Written against the code, not against the intention. Where a safeguard is partial, this
page says which part.

## What leaves your machine

Two destinations, and only two.

**The model provider.** Every turn's prompt goes to OpenRouter, at
`https://openrouter.ai/api/v1` unless `OPENROUTER_BASE_URL` names another. What goes
with it is the whole of what the model needs to answer: cora's brief, the instructions
of whichever plugins are loaded for that field, the facts you asked cora to remember,
the last twenty turns of this conversation, and the results of every tool the turn
called — which includes the passages a document search returned. If cora answers from
your documents, the words of those passages reach the provider. That is what answering
from them means.

Routing sends one extra call when a deployment loads more than one field: the question,
and the first line of each field's instructions, so the model can say which field the
question belongs to. A delegated loop — the travel researcher — sends its own rounds.

What the provider then does with it is theirs to state, not cora's; OpenRouter routes to
whichever upstream model you named, and its terms are the ones that apply.

**A service a plugin calls.** The travel plugin fetches forecasts from
`geocoding-api.open-meteo.com` and `api.open-meteo.com`, sending the place name and the
dates you asked about. It needs no credential. Every other outbound call in this
repository belongs to a plugin you chose to load, and a plugin can call anything —
see [what loading a plugin costs](#what-loading-a-plugin-costs-in-trust).

**Embedding is local.** The model that turns your documents into vectors,
`sentence-transformers/all-MiniLM-L6-v2`, runs on your machine and downloads once from
Hugging Face on first use. No document text is sent anywhere to be indexed.

## What is kept, and where

Everything cora keeps is a file on your own machine. Each has its own setting so one can
be moved without moving the others.

| Where | What is in it | Setting |
| --- | --- | --- |
| `.cora/documents` | The cleaned text of every document you uploaded, one Markdown file per upload, under a directory per field | `CORA_DOCUMENTS_PATH` |
| `.cora/chroma` | The embeddings, and where each passage sits in the file above | `CORA_DB_PATH` |
| `.cora/memory.sqlite` | The facts you asked cora to remember | `CORA_MEMORY_PATH` |
| `.cora/conversations.sqlite` | Every recorded turn — question, answer, citations, trace — and the checkpoints a paused turn is resumed from | `CORA_CONVERSATIONS_PATH` |
| `.cora/logs/cora.log` | Written only under `CORA_DEBUG`: prompts, replies and retrieved passages, each cut to 120 characters | `CORA_LOG_PATH` |
| `cora-output` | What an approved effect produced — an itinerary you said yes to | `CORA_OUTPUT_PATH` |
| `.cora/plugins/` | Single-file plugins you dropped in yourself | `CORA_PLUGINS_PATH` |

Nothing here is encrypted, and nothing is deleted on your behalf. `.cora/` is cora's own
bookkeeping and a deployment may delete it to start clean; `cora-output` is deliberately
outside it, because a file you approved is yours rather than cora's.

Your API key is read from the environment. It is never written to any of these, and never
logged.

## What the model is told, and what it is not

The prompt is assembled fresh each turn: cora's own brief, then the loaded plugins'
instructions for that field, then your remembered facts, then the conversation, then the
tool results. Nothing else. cora holds no profile of you beyond the facts you asked it to
keep, and you can read and delete those from the page.

A question the screen refuses never reaches the model at all.

## Where the safeguards stop

**The injection screen reads your question, and nothing else.** It is two regular
expressions. One catches "ignore the previous instructions"-shaped phrasings, the other
"reveal your system prompt"-shaped ones. That is the whole of it.

It does not scan the text of your uploaded documents, it does not scan what a tool
returned, and rewording gets past it — anyone who wants to phrase an injection
differently can. It raises the cost of the laziest attempt and nothing more. Treat it as
a speed bump, not a wall.

**The untrusted-data label is for the model, and the model can still be led.** Anything
that came out of your documents, out of a service a tool called, or out of a tool that
read either, reaches the model behind a notice telling it to treat the material as
evidence only and never to follow instructions found inside it. That label is applied by
cora's core and no plugin can take it off. But it is a sentence addressed to a language
model, not an enforcement boundary: a document containing "ignore your instructions" is
still a document the model reads. If you upload text you did not write, you are trusting
the model's compliance with that notice.

**The approval gate covers what was declared to cora.** A tool a plugin registered with
`effect=True` cannot run on the model's word. The turn stops, you see what the tool says
it does and the arguments the model wrote, and nothing outside cora happens until you
approve. Decline and the tool is never called.

What the gate cannot see is what a plugin's own code does *inside* a call it was allowed
to make. A tool that declares no effect and writes a file anyway will write it. The gate
is a promise about the calls cora knows about, which is every call it was told about.

**Where an answer can simply be wrong.** Retrieval can miss the passage that held the
answer; a document can be out of date, and cora has no idea when it was true; the model
can misread a passage it was given correctly; a forecast is a snapshot of one moment; and
with more than one field loaded, the router can answer in the wrong one. Citations are
what make this checkable — every `[n]` opens onto the passage it came from, so you can
read the source rather than trusting the summary. Do that for anything that matters.

## What loading a plugin costs in trust

**A plugin is arbitrary code running with your permissions.** Not a sandboxed extension,
not a manifest of capabilities — a Python module that cora imports and calls. It can do
anything you can do on that machine: read any file you can read, open any network
connection, run any subprocess. This is true of every harness of this kind, cora
included, and pretending otherwise would be the dishonest version of this page.

Through the contract it is offered, a plugin contributes four things:

- **instructions** — text that heads its section of the model's brief, which the model
  then follows
- **tools** — named functions the model may call, with arguments the model writes
- **handlers** — code at one of four points in a turn (`screen`, `brief`, `tool_call`,
  `tool_result`) that can refuse the question, amend the brief, refuse a call, or change
  what a tool returned before the model sees it
- **effects** — tools declared as changing something outside cora

`make plugins` prints exactly what each loaded plugin registered, and the plug icon on
the page shows the same listing. Read it before you trust a plugin, and read its source
if the plugin came from someone you do not know.

### What cora enforces whatever a plugin does

- **An effect waits for you.** The gate is a step of cora's core standing on the only
  path from the model to its tools. A plugin cannot subscribe to it, switch it off or
  imitate it, and no handler can pause a turn.
- **The untrusted label stays on.** Retrieved passages and fetched text reach the model
  behind that notice, and no plugin can remove it.
- **Output is confined.** A plugin writing what an effect produced is handed a port, not
  a path. A filename that would resolve outside the configured output directory is
  refused, so no plugin writes that check itself.
- **Three tool names are cora's.** `search_documents`, `remember` and `ask_user` cannot
  be taken by a plugin; a plugin that tries is refused at startup rather than shadowing
  the tool the model expects.
- **A screen cannot be scoped away.** A handler registered system-wide runs in every
  turn, whatever field the turn is in, so an injection screen holds for all of them.

### What cora does not enforce

- **No sandbox.** Nothing restricts what a plugin's code may do once loaded.
- **No network restriction.** A plugin may call any host, with or without a credential
  of its own.
- **No review of instructions.** What a plugin's instructions tell the model is text cora
  puts in the brief unread. A plugin can shape the persona, the priorities and the tone
  of every answer in its field.
- **No isolation between plugins.** Load order is the only precedence there is, and
  plugins share the stores.

The honest summary: cora enforces what it can see at the seam it defined, and loading a
plugin is a decision to trust its author. The listing tells you what a plugin claims; only
its source tells you what it does.
