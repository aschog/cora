# Privacy, and what a plugin costs in trust

Two costs, on one page. Uploading your documents to cora sends some of them to a model
provider and keeps the rest on your disk. Loading somebody else's plugin runs their code
with your permissions. Neither is hidden and neither is free, so here is what each one
actually is.

Written against the code, not against the intention: every claim below was read off the
source at the commit this page ships in. Where a safeguard is partial, this page says
which part.

## What leaves your machine

Three hosts, and no others: two your data goes to, and one cora fetches from.

**The model provider.** Every turn's prompt goes to OpenRouter, at
`https://openrouter.ai/api/v1` unless `OPENROUTER_BASE_URL` names another. What goes
with it is the whole of what the model needs to answer: cora's brief, the instructions
of whichever plugins are loaded for that field, the facts you asked cora to remember,
the last twenty messages of this conversation — or as many as `CORA_HISTORY_TURNS`
says — and the results of every tool the turn called — which includes the passages a document search returned. If cora answers from
your documents, the words of those passages reach the provider. That is what answering
from them means.

Routing sends one extra call when a deployment loads more than one field: the question,
and the opening paragraph of each field's instructions, so the model can say which field
the question belongs to. A delegated loop — the travel researcher — sends its own rounds.

What the provider then does with it is theirs to state, not cora's; OpenRouter routes to
whichever upstream model you named, and its terms are the ones that apply.

**A service a plugin calls.** The travel plugin fetches forecasts in two calls: the
place name goes to `geocoding-api.open-meteo.com`, and the coordinates that comes back
with, plus your dates, go to `api.open-meteo.com`. It needs no credential.

The same plugin prices a trip through `serpapi.com`, which is a search proxy over what
Google shows for flights and hotels. That call carries more about you than a forecast
does: where you are flying from, where you are going, the dates you are considering and
the ceiling you set. It carries a key, so the searches are attributable to whoever holds
the account. cora offers the two searches only where a deployment set
`CORA_PLUGIN_TRAVEL_SERPAPI_KEY`, so a deployment that sets nothing makes no such call —
and what SerpApi keeps is theirs to state, not cora's.

Every other outbound call in this
repository belongs to a plugin you chose to load, and a plugin can call anything —
see [what loading a plugin costs](#what-loading-a-plugin-costs-in-trust).

**Hugging Face, once.** The model that turns your documents into vectors,
`sentence-transformers/all-MiniLM-L6-v2`, is downloaded from Hugging Face the first time
cora indexes anything, and then runs on your machine. That call fetches; it sends nothing
of yours, and no document text is sent anywhere to be indexed. A deployment that wants no
outbound call at index time needs the model cached before it starts.

Nothing else in cora phones home. The vector store's own telemetry is a no-op in the
version pinned here, and a version bump is a reason to check that again.

## What is kept, and where

Everything cora keeps is a file on your own machine. Each has its own setting so one can
be moved without moving the others.

| Where | What is in it | Setting |
| --- | --- | --- |
| `.cora/documents` | The cleaned text of every document you uploaded, one Markdown file per upload, under a directory per field | `CORA_DOCUMENTS_PATH` |
| `.cora/chroma` | The embeddings, and where each passage sits in the file above | `CORA_DB_PATH` |
| `.cora/memory.sqlite` | The facts you asked cora to remember | `CORA_MEMORY_PATH` |
| `.cora/conversations.sqlite` | Every recorded turn — question, answer, citations, trace — and a checkpoint of every turn's state: the brief, the transcript, and the tool results the model was shown | `CORA_CONVERSATIONS_PATH` |
| `.cora/logs/cora.log` | Written only under `CORA_DEBUG`. cora's own lines cut each prompt, reply and passage to 120 characters; see below for what is not cut | `CORA_LOG_PATH` |
| `cora-output` | What an approved effect produced — an itinerary you said yes to | `CORA_OUTPUT_PATH` |

`.cora/plugins/` is the one location cora reads rather than writes: single-file plugins
you dropped in yourself, moved by `CORA_PLUGINS_PATH`.

The 120-character cap is cora's own, and it covers the three kinds of line above and
nothing else. A malformed tool call is logged with the arguments the model wrote, in
full; a provider failure is logged with its traceback; and every loaded plugin gets a
logger under cora's own, so a plugin's log lines land in the same file, uncapped, saying
whatever that plugin chose to say.

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

A question the screen refuses never reaches the model at all — where a screen is
loaded, which is the first thing the next section is about.

## Where the safeguards stop

**There is no screen unless the deployment asked for one.** cora loads no plugin unless
it is named, and the injection screen is a plugin: `cora.plugins.security`. A cora
started without it in `CORA_PLUGINS` reads nothing at all before the model does. It says
so in the log at startup — *no plugin screens what the user types* — and nowhere else, so
check what you are running. The quick start in `README.md` names it; a deployment that
copied only half of that line does not have it.

**The screen, where it is loaded, reads your question and nothing else.** It is two
regular expressions. One catches "ignore the previous instructions"-shaped phrasings, the other
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

Its boundary is also the word *outside*: a tool that changes something of cora's own —
your remembered facts, say — is not an effect by this definition and does not wait for
you.

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

And this is what cora *hands* a plugin, through the contract rather than around it —
the well-behaved-plugin case, which matters as much as the malicious one:

- **your documents.** A plugin can search the index directly and read back the passages
  of whatever field the turn is in.
- **what cora remembers.** A plugin can read your remembered facts, add to them, delete
  one, or clear the lot. None of that is gated: the approval gate covers effects
  *outside* cora, and cora's own stores are inside it.
- **the model.** A plugin can send anything it holds to the provider, either directly or
  by delegating a bounded loop of its own.

`make plugins` prints exactly what each loaded plugin registered, and the plug icon on
the page shows the same listing. That tells you what a plugin *claims*; only its source
tells you what it does. Read the listing before you trust a plugin, and read the source
if it came from someone you do not know.

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
- **A system-wide handler cannot be scoped away.** A handler registered without a scope
  runs in every turn, whatever field it is in, and no scope can switch it off — so a
  screen that *is* loaded covers every field. cora does not enforce that one is loaded;
  that is the deployment's to get right.

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
