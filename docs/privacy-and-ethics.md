# Privacy, and what a plugin costs in trust

Two costs. Uploading your documents sends some of them to a model provider and keeps the
rest on your disk. Loading somebody else's plugin runs their code with your permissions.
Every claim below was read off the source, and where a safeguard is partial it says
which part.

## What leaves your machine

- **The model provider.** Every turn's prompt goes to OpenRouter, at
  `https://openrouter.ai/api/v1` unless `OPENROUTER_BASE_URL` names another. With it
  goes cora's brief, the loaded plugins' instructions for that field, your remembered
  facts, the last twenty messages of the conversation — or as many as
  `CORA_HISTORY_TURNS` says — and every tool result, which includes the words of any
  passage a document search returned. Answering from your documents means sending them.
- **One extra call to route**, where more than one field is offered and nothing pins the
  turn: the question, and the opening paragraph of each field's instructions. A
  delegated loop sends rounds of its own — travel has two, the researcher and the
  planner, and the planner runs one per revision pass.
- **A service a plugin calls.** Travel fetches a forecast in two credential-free calls,
  the place name to `geocoding-api.open-meteo.com` and the coordinates with your dates
  to `api.open-meteo.com`. It prices a trip through `serpapi.com`, which carries where
  you are flying from, where to, the dates you are considering and your ceiling — unless
  `CORA_PLUGIN_TRAVEL_SEARCH_URL` names another host. The key rides in the query string,
  so it reaches whatever host that is, and makes the search attributable. Both searches
  exist only where `CORA_PLUGIN_TRAVEL_SERPAPI_KEY` is set.
- **Hugging Face, once.** `sentence-transformers/all-MiniLM-L6-v2` is downloaded the
  first time anything is embedded — an upload or a search — and then runs locally, so no
  document text is sent anywhere to be indexed. An offline deployment pre-caches it.
- **Telegram, where the bot is run.** `make bot` polls `api.telegram.org` and posts its
  answers back there: the answer itself, the names of the documents it cites, and a
  card's prompt with the values it already holds. The question arrives from Telegram
  rather than going to it, because it was typed there. Only the chats
  `CORA_TELEGRAM_CHATS` names are answered, and the bot token rides in every URL, so
  it is a credential the same as any other. Nothing is sent where the page is run
  instead.

**The fitness trainer**, being a page, reaches from your browser rather than from cora:
`docs.google.com` for the published sheet its plan comes from and `i.ytimg.com` for an
exercise thumbnail — both on load, before you touch anything — and `cdn.jsdelivr.net` with `storage.googleapis.com` for the pose runtime,
only once you turn tracking on. A clip plays from `www.youtube-nocookie.com`, which sets
no cookie until you play one, and only when you open a clip. The workout it saves goes to
cora and nowhere else.

Nothing else in cora reaches the network: no general-purpose HTTP client — `httpx`,
`requests`, `urllib` — is imported anywhere under `src/cora`, no telemetry package is in
the tree or the lockfile, and the only outbound clients there are the provider's and the
embedder's, both named above. Every other outbound call belongs to a frontend or a
plugin you chose to run, and a plugin can call anything.

## What is kept, and where

| Where | What is in it | Setting |
| --- | --- | --- |
| `.cora/documents` | The cleaned text of every document you uploaded, a Markdown file per upload under a directory per field | `CORA_DOCUMENTS_PATH` |
| `.cora/cora.sqlite` | The passage spans and their vectors, the facts you asked cora to remember, every recorded turn — question, answer, citations and the whole trace, which carries each tool call's arguments and all of what it returned, retrieved passages included — and a checkpoint of every turn's state | `CORA_DB_PATH` |
| `.cora/logs/cora.log` | Written only under `CORA_DEBUG` | `CORA_LOG_PATH` |
| `cora-output` | What an approved effect produced | `CORA_OUTPUT_PATH` |
| `.cora/plugins` | Plugins you dropped in — read, imported and executed | `CORA_PLUGINS_PATH` |

How the file is divided: [where your data lives](data-storage.md).

- cora's own log lines cut each prompt, reply and passage to 120 characters. Three
  things are uncapped: a malformed tool call's arguments in full, a provider failure's
  traceback, and every loaded plugin's own lines, because a plugin's logger hangs under
  cora's.
- Nothing is encrypted, there is one user, and there is no backup. `.cora/` is
  bookkeeping a deployment may delete; `cora-output` is outside it because a file you
  approved is yours.
- Your API key is read from the environment, never written to any store and never
  logged. Absent, cora refuses to start.
- Four things you can delete, each asking first, each saying what is lost and what is
  kept, none undoable: a document, a conversation, a fact, and a plugin. Deleting a plugin is the one that cascades — the
  documents of every field only it brought, their passages, and every conversation
  pinned there. What cora remembers, and what an effect wrote, are left. An answer keeps
  the citations it was given and says the document is gone when you open one.

## Where the safeguards stop

**There is no authentication.** Every route — documents, ask, resume, sessions, memory,
plugins — is open to whoever can reach the port, and `CORA_HOST` moves it off the
loopback default. A deployment that does that has published its documents, its
conversations and its approval gate.

**There is no injection screen unless the deployment loaded one.** cora starts with no
plugins, and the screen is `cora.plugins.security`. cora's own screening reads every
question but only for shape: blank is refused, and over 4000 characters is refused —
nothing about content.

**The startup warning is not a test for it.** *no plugin screens what the user types*
fires only when no plugin at all registers a screening handler, so a deployment loading
the fitness plugin's medical filter silences the warning while nothing screens for
injection. Check what you loaded, not what the log said.

**The screen, where it is loaded, is two regular expressions** — one for "ignore the
previous instructions", one for "reveal your system prompt". It subscribes to the
question alone, so it never sees your documents or what a tool returned, and a reworded
injection gets past it. A speed bump, not a wall.

**The untrusted label is for the model.** A passage, a service's reply, or a tool that
read either reaches the model behind a notice telling it to treat the material as
evidence only. The flag is recorded by the runtime before any `tool_result` handler sees
the result, so no plugin can take it off — but it is a sentence addressed to a language
model, not an enforcement boundary. Upload text you did not write and you are trusting
the model's compliance.

**A card's prompt and boxes are somebody's own words.** cora's own form is the model's:
it names the fields, their labels and their types — two to twelve of them, strings,
numbers and booleans. A card a plugin's tool puts up is that plugin's, with no field
count or type limit; cora refuses only one that asks for a single value. Either way cora
settles it with you before the tools run, so no `tool_call` handler sees it and the
shipped screen never reads it. Read the first the way you read the answer above it, and
the second the way you read the plugin.

**The approval gate covers what was declared to it.** A tool registered `effect=True`
cannot run on the model's word — [what cora does](what-it-does.md#effects-and-the-gate-they-wait-at)
is the account. An unanswered proposal is declined, and no handler can pause a turn. But
a tool that declares no effect and writes a file inside its own code writes it, and
"outside" is the boundary: cora's own `remember` writes your facts with no gate at all.

**Where an answer can simply be wrong.** Retrieval can miss the passage that held the
answer; a document can be out of date; the model can misread a passage it was given
correctly; a forecast is one moment; and with more than one field loaded the router can
answer in the wrong one. Citations are what make this checkable.

## What loading a plugin costs in trust

**A plugin is arbitrary Python that cora imports and calls with your permissions.** No
sandbox, no network restriction, no review of the instructions it puts in the brief, no
isolation between plugins, and load order is the only precedence. What is dropped in
`.cora/plugins` is executed, a folder holding `__init__.py` counts as one, and the folder
is re-read live — so code added while cora serves runs on the next request.

It contributes four registrable kinds: a tool, instructions, a handler at one of five
points (`screen`, `brief`, `tool_call`, `tool_result`, `answer`), and a page. An effect
is a flag on a tool, not a fifth kind.

**A page is the one of the four that is not Python.** A plugin names a directory of its
own and cora serves it whole, on cora's own address, to whoever reaches the port —
everything under it, so a key or a build artefact left there is published. What runs in
it is the plugin's JavaScript in your browser, on the origin the rest of cora answers
from: there is no password between it and any route on this page, and it reaches the
camera, the microphone and the storage your browser would give cora itself.

And cora hands it, through the contract: the document index of the turn's field, the
memory port — read, add, forget one, clear all, none of it gated — the model, a
per-conversation store of its own, and a trace line cora signs with its name.

What cora enforces whatever a plugin does:

- An effect waits at a step of the core no plugin can subscribe to or switch off. The
  *step* is what is enforced, and not that the yes is yours: a plugin's page can read
  the waiting card over the same unauthenticated API you answer it on, and answer it
  itself. A plugin's own tool can also put up a card that *looks* like the gate's — cora
  draws every card with one component — so what tells you the gate ran is the trace, not
  the card.
- An effect tool is never offered to a delegated loop, so an effect stays in the turn you
  are watching. A tool that asks is withheld the same way.
- The untrusted label stays on.
- Output is confined: a plugin is handed the port, not a path, and a name resolving
  outside the root — via `..`, an absolute path or a symlink — is refused after
  resolution.
- Four tool names are cora's — `search_documents`, `remember`, `ask_user`,
  `ask_user_for` — and a plugin registering one is refused at startup.
- A handler registered without a scope runs in every turn and no scope can switch it
  off, so a screen that *is* loaded covers every field. That one is loaded is the
  deployment's to get right.

A page is not contained, and deliberately so: the same origin is what lets it call cora
without a token of its own, and a frame with no origin would lose both that and the
camera. So a page is exactly as trusted as the plugin that brought it.

`make plugins` and `GET /api/plugins` print what each loaded plugin registered — what it
claims, not what it does. Read the listing before you trust a plugin, and the source if
you do not know the author.
