# Write a plugin

A plugin gives cora a persona, tools, a hand in the turn — or any one of the three.
Drop it in `.cora/plugins` and it is loaded: [load plugins](load-plugins.md) is the
folder's own rules. What the names below promise is
[`cora.ports.host`](../api/cora/ports/host/index.md).

## The whole of it

`field_notes.py`, dropped in the folder, is the `field_notes` plugin:

```python
from cora.ports.host import Host

CONTRACT = 1

INSTRUCTIONS = """You keep a field notebook. Answer from the notes, and say when they
are silent rather than filling the gap."""

SCHEMA = {
    "type": "object",
    "properties": {"species": {"type": "string"}},
    "required": ["species"],
}


def extend(cora: Host) -> None:
    cora.register_instructions(INSTRUCTIONS, scope="notes")
    cora.register_tool(
        name="count_sightings",
        description="How many passages of the notes mention one species, up to 20.",
        parameter_schema=SCHEMA,
        run=lambda species: len(cora.documents.search(species, k=20)),
        scope="notes",
    )
```

- cora looks for an attribute named `extend` and calls it once per app with a host of
  the plugin's own. No `extend`, or one that is not callable, and the plugin is refused
  by name. For a folder that attribute is `__init__.py`'s, so you may define it in a
  submodule and re-export it.
- `Host` is a Protocol: the annotation is documentation, and nothing checks it.
- Instructions become one section of the model's brief, headed by cora with your
  plugin's name. Its first *paragraph* is what the router is given to choose a field
  with, so open by saying what the field answers.
- `CONTRACT` is the version you want, written as a literal — importing cora's makes the
  check pass whatever it says. Left off, it reads as asking for whatever cora offers.
  cora offers `1`; another number is refused, naming both. Surface is added without the
  number moving; a change to what a name promises moves it. The module body runs before
  the check, so import side effects happen either way.
- The name is the file's, or the folder's for a directory holding `__init__.py`. It has
  to be a plain identifier, because it also spells the plugin's settings:
  `CORA_PLUGIN_FIELD_NOTES_UNITS` reaches it as `units`.
- Nothing is installed for a drop-in. An import cora's environment lacks refuses the
  plugin, so a plugin with dependencies of its own is a workspace package —
  `plugins/travel` is that shape, importable once the root names it in
  `[tool.uv.sources]` and `[dependency-groups] dev`. It still loads by being in the
  folder: this repository's own three are symlinks into it.

## Tools

`register_tool` takes `name`, `description`, `parameter_schema`, `run`, and keywords for
what the tool is:

- `scope="notes"` — offered only in that field, and the field exists because something
  registered under it: `notes` reaches the picker, the router and the rails with the
  plugin, and goes with it. Left off, the tool is offered in every turn and no field can
  switch it off.
- `untrusted=True` — what it returns reaches the model behind the label a document
  passage carries. Declare it for anything the plugin did not write itself.
- `effect=True` — it changes something outside cora, so the turn stops and the reader
  approves the call before `run` is reached. Declined, it never runs.
- `asks=…` — the card below.

`register_tool` refuses a blank name, a `run` that is not callable, an invalid schema,
and a name this plugin already registered. A name that is one of cora's four
(`search_documents`, `remember`, `ask_user`, `ask_user_for`) or another loaded plugin's
is refused when the registry is composed.

`run` is called with the arguments the model wrote, validated against the schema you
registered. Raise `ToolRefusal` from `cora.ports.plugin` and the model reads
`tool '<name>' failed:` and your sentence; raise anything else and it reads the same
prefix and the exception's class name, nothing more.

## Cards

A tool may declare `asks`: a function handed a copy of the arguments as written,
answering with a card to put to the reader, or `None` to run as called. Pass it as
`asks=asks` beside the schema it is built from.

```python
from cora.domain.card import ActionOffered, Card, fields_of, missing_from

def asks(arguments: dict) -> Card | None:
    if not missing_from(SCHEMA, arguments):
        return None
    return Card(
        prompt="Give me the trip and I'll price it.",
        fields=fields_of(SCHEMA, arguments),
        actions=(
            ActionOffered(label="Search", answer="Search", needs_valid=True),
            ActionOffered(label="Not now", answer=None),
        ),
    )
```

- Build the fields from the schema you registered, so the two cannot drift. A field's
  own schema picks its control: `format: "date"` draws a date input, a short `enum` a row
  of choices, and anything the page cannot draw falls back to text. The model is
  offered that schema with `required` stripped, because the card is what requires it —
  but the call is validated against the schema as registered, so a card that leaves out
  a required argument can only produce a refused call.
- What the reader writes is written over the arguments, and `run` is called once, with
  those.
- A card needs an action, and not every action may wait on the fields — a card nobody
  can leave is refused. `answer=None` is the way out.
- `needs_valid` only disables the button, so write the tool to refuse a call it cannot
  run.
- cora refuses a card asking for exactly one writable value, and tells the model to ask
  for it in its answer instead. A card asking for *nothing* — read-only rows and a yes —
  stands, and left unconfirmed the call does not run.
- `asks` has to be pure. The step that puts your card is replayed every time the turn is
  picked up, and cora calls `asks` again with the same arguments. One that raises, or
  answers with something that is not a `Card`, costs the call and not the turn.

## A page

`register_page(directory, scope=…)` gives one field a page of its own. cora serves the
directory whole at `/pages/<field>/`, `index.html` first, and hands that address to
whatever is drawing the screen.

```python
import pathlib


def extend(cora: Host) -> None:
    cora.register_instructions(INSTRUCTIONS, scope="notes")
    cora.register_page(pathlib.Path(__file__).parent / "page", scope="notes")
```

- The field is required, where every other registration may leave it off: a page belongs
  to a subject, and there is no page for every turn. Two plugins bringing one field's
  page is refused when they are composed, naming both.
- The directory is read at the request, not at registration. One that is not there costs
  that address a refusal and nothing else — the rest of the plugin loads and answers.
- It is served live, like everything else in the plugins folder: edit a file and the next
  request has it, and a directory that was missing at load serves as soon as it is there.
- **Everything under the directory is public** to whoever reaches cora's port, so put
  nothing there you would not publish. A symlink pointing out of the directory is not
  followed.
- The page is served on cora's own origin, so it may call the API with no token — and
  every route the reader has, it has. That is the same trust loading the plugin already
  extended, and [privacy](../privacy-and-ethics.md#what-loading-a-plugin-costs-in-trust)
  says so plainly.
- A page may ask the shell for the whole screen, and let it go again, by posting
  `{cora: 'screen', wanted: true}` — or `false` — to its parent window on cora's own
  origin. While it wants it and the reader has folded both rails, what is left of the
  rails is not drawn and the frame is the whole screen, so the page is what closes that
  state: let go when what wanted it ends, and as your page goes. The reader can take the
  screen back with Escape at any time, so hold nothing on having it. The trainer asks on
  its camera's first frame, and lets go when it closes or its picture is taken away.

## Handlers

`register_handler(event=…, handle=…, scope=…)` subscribes to one of the five points in
`cora.ports.host` — `SCREENING`, `BRIEFING`, `CALLING`, `RETURNING` and `ANSWERING`,
which carry the strings `screen`, `brief`, `tool_call`, `tool_result` and `answer`. An
unknown name is refused. Your handler is called with one value and
its return is the whole of its decision — `None` changes nothing, at every event.

| event | handed | a return |
| --- | --- | --- |
| `SCREENING` | the question | a `str` refuses the turn, and the reader reads it |
| `BRIEFING` | the brief | a `str` replaces it |
| `CALLING` | a `ToolCall` | a `str` refuses that call, and the model is told why |
| `RETURNING` | a `ToolResult` | a `ToolResult` replaces what the model is told |
| `ANSWERING` | the answer, once per turn | a `str` replaces what is recorded and handed back |

- `scope` behaves as it does on a tool: left off, the handler runs in every turn and no
  field can switch it off — which is what an injection screen needs.
- Fail closed where the event refuses, open where it amends. A wrong type or a raise is
  dropped at `BRIEFING`, `RETURNING` and `ANSWERING`, and refuses at `SCREENING` and
  `CALLING` — a `SCREENING` handler that breaks refuses on cora's own wording.
- `ANSWERING` amends and cannot refuse. No handler can pause a turn: stopping to ask is
  the core's.
- `CALLING` is handed a copy, so writing into the arguments changes nothing that runs. A
  `RETURNING` result is read for its payload or error — exactly one of them, or the
  amendment is dropped — and the call it answers is cora's to say.

## What the host hands you

- `cora.documents.search(query, k)` — the field the turn is running in, and no other. It
  answers with the top of the ranking whatever the scores, so a count of what came back
  is a count of that, not of what matched.
- `cora.documents.all()` — every document that field holds, each with its `name`, its
  `text` and its `scope`, the uploads of one name together and oldest first. Two uploads
  of one name are two documents, and one whose file is gone is left out. Read it when
  the question is "all of them" rather than "which ones match": a search ranks and cuts,
  a reading hands over the shelf.
- `cora.memory` — what cora keeps about the user, and `None` where the deployment has
  none. Check before you use it.
- `cora.model` — the model, for a plugin that needs one directly.
- `cora.settings` — this plugin's own variables, as strings.
- `cora.output` — where an approved effect writes. May be absent, so a tool that writes
  should not be registered without it. `write(name, text)` answers with where the file
  landed, and refuses a name that would climb out of it.
- `cora.state.keep(name, text)` / `read(name)` — text kept between the turns of one
  conversation, under names no other plugin shares, gone when it is deleted. A read
  answers `str | None`, and `keep(name, None)` is how a name is dropped. Bound inside a
  tool call only: elsewhere a read is empty and a write is dropped.
- `cora.store.keep(name, text)` / `read(name)` — text kept for good, under the plugin's
  own name: it outlives the conversation, the process and a restart, where `cora.state`
  outlives none of them. `keep(name, None)` drops a name, and a name nothing was kept
  under reads as `None`. Absent where the deployment keeps no file, so check it before
  you write. What a plugin keeps here is the plugin's own: nothing searches it, cites
  it, recalls it or puts it in a brief.
- `cora.delegate(task, tools=(), rounds=3, shape=None)` — a bounded loop of its own with
  the model, offered what you pass plus cora's document search. Tools declaring `effect`
  or `asks` are withheld, and a tool of yours named `search_documents` fails the call.
  `rounds` is capped at five, one more than asked reaches the model, and a loop that
  gathered nothing fails rather than spending a call.
- `shape=` is JSON Schema the answer must satisfy, and what you get back is the value
  rather than prose. The loop is offered one more tool, `answer`, whose parameters are
  your shape — so the schema is put to the model as a schema, and an answer that fails
  it is told to the loop, which corrects it in a round it already had. It costs no round
  prose would not have cost. A tool of yours named `answer` fails the call, the shape
  must require something, and prose where the shape was asked for fails the call rather
  than coming back as a guess. `format` is not checked, so read your own dates.
- `cora.show(did, detail="", failed=False)` — one line on the trace, signed with your
  plugin's name, under the call it was said inside.
- `cora.log` — a logger named for the plugin.

A registered tool closes over the host it was registered with, which is how it still has
a cora to search or delegate with when the model calls it.

## What refuses your plugin

At load: no `extend`, a name that is not an identifier, a name two plugins share, a
contract cora does not offer, an import it cannot satisfy, an invalid schema, a tool
name that is cora's. Raise `PluginLoadError(name, reason)` from `cora.domain.errors` to
refuse it yourself; any other exception escaping `extend` reaches the operator as its
class name alone.
