# cora

![CoRa: one core, endless plugin power](docs/assets/cora.png)

## Why

An agent that is good at your subject usually means somebody built an app for that
subject. Cora turns that around: the agent is the part that stays, and the subject is
the part you build yourself — a fitness coach, a trip, a lab notebook.

## With nothing loaded

It answers, and it works in its field: it reads a file there, writes one, and runs a
command in that directory. That is all it has of its own. Searching your documents,
remembering what you tell it, stopping to ask you — each of those arrives as a plugin,
and the three cora ships are the first three in the loop below. It changes nothing
outside its field unless a plugin gave it something that does.

## A field can bring a screen

A plugin may hand cora a page of its own, and cora serves it at its field's address. The
fitness plugin brings one: a kettlebell trainer that logs the workout you just did into
the field, where the coach can answer from it. Pin the field and it fills the screen,
with the conversation beside it.

## One cora, many subjects

A plugin's things live in a field of its own. One SQLite file holds cora's own
bookkeeping and partitions a field's vectors apart from every other field's,
`.cora/fields` is a directory per field holding what lands there — every upload, as the
file it arrived as, beside whatever that field's plugin keeps — and `.cora/documents` is
a directory per field holding the cleaned text a citation opens onto. A second subject
is a second directory, not a second store. That is the whole layout.

## Start here

```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
```

Symlink the plugins you want into `.cora/plugins`, then run it:

```sh
mkdir -p .cora/plugins
# The first three are what a bare cora has none of: searching, remembering, asking.
for each in documents memory ask security fitness interview travel vocab; do
  ln -s "$(pwd)"/plugins/$each/src/cora/plugins/$each .cora/plugins/$each
done

export OPENROUTER_API_KEY=sk-or-...
make run                                   # or: make run-env, to read the key from .env
```

`make run` builds the page and serves it with the API from one process on
127.0.0.1:8000. `make bot` runs the Telegram bot instead.

The gates, which the pre-commit hook and CI both run:

```sh
uv run pytest
uv run ruff format . && uv run ruff check . && uv run ty check
npm --prefix frontends/react/ui run lint && npm --prefix frontends/react/ui test
```

## Network access

Local startup stays on loopback and needs no access token. Binding beyond loopback
requires `CORA_NETWORK=1` and a nonblank `CORA_API_TOKEN`; setting a token alone does
not enable network access. `CORA_NETWORK` accepts only `1`, `0`, or an unset/blank value.

Set a long, random `CORA_API_TOKEN` in your environment first, then run:

```sh
export CORA_NETWORK=1
export CORA_HOST=0.0.0.0
make run
```

Alternatively, put these settings alongside the model key in your ignored `.env` and
use `make run-env`. Never commit that file, print the token, or put it in a URL.
`CORA_PORT` selects the port, defaulting to 8000.

Opening cora from another device brings up the browser's native login prompt. Use
`cora` as the username and the API token as the password. API clients use the same
HTTP Basic credentials; Bearer tokens are not accepted. For example, this asks for
the token rather than including it in the command:

```sh
curl --user cora http://your-machine:8000/api/scopes
```

Every HTTP route is protected, including the built page, plugin pages, documents,
uploads, field files, memory, conversations, and notices. The token grants full
operator access: holders can upload, write, delete, and ask the model to run shell
commands. This is one shared operator credential, not accounts or a multi-user
permission system. Browser mutations must come from the same origin; authenticated
native clients without an Origin header still work.

**Use HTTPS for production.** Basic authentication does not encrypt the token or
traffic over HTTP; use plain HTTP only on a network you trust. For HTTPS termination,
keep cora behind a trusted proxy, preserve the original Host, and forward the public
scheme. Uvicorn trusts forwarded headers from `127.0.0.1` by default; if your proxy
is elsewhere, set `FORWARDED_ALLOW_IPS` to only its addresses, never `*`. Enable
`CORA_NETWORK=1` even when the proxy reaches a loopback-bound cora, or that upstream
will remain unauthenticated.

Changing the token requires restarting cora. Browsers may cache Basic credentials;
clear them or use a fresh browser session when switching tokens. The server itself
keeps no login sessions.

### Watch support is deferred

The existing `make run-watch` selects a public binding but does not opt into network
mode, so it now refuses startup unless network settings are supplied explicitly.
The current watch extension sends no credentials, so its notice requests are refused
in network mode even if the server is started. Restricted watch credentials and build
support are tracked separately in `docs/backlog.md`; there is no unprotected notice
exception and no change to the watch extension in this feature.

## Write a plugin

Drop a `.py` file, or a folder with an `__init__.py`, into `.cora/plugins/`. It is named
for the file or folder, needs no packaging, and the folder is live — dropped, edited or
deleted, the next request has it. Nothing is installed for a drop-in, so it may import
only cora and the standard library.

All it must export is `extend`:

```python
import pathlib

from cora.ports.host import SCREENING, Host

SCOPE = "recipes"          # the field it owns; omit to register system-wide

def extend(cora: Host) -> None:
    cora.register_instructions("Answer as a cook, from the user's own notes.", scope=SCOPE)
    cora.register_tool(name=..., description=..., parameter_schema=..., run=..., scope=SCOPE)
    cora.register_handler(event=SCREENING, handle=...)
    cora.register_page(pathlib.Path(__file__).parent / "page", scope=SCOPE)
    cora.register_files(scope=SCOPE)   # the field's files are yours, not a workspace
```

Register what you need and nothing else — `plugins/security` is a handler alone,
`plugins/fitness` is four of the five. Settings arrive by name:
`CORA_PLUGIN_RECIPES_API_KEY` reaches it as `api_key`. `make plugins` prints what loaded
and what each one registered.

A field is a workspace: cora reads, writes and runs a command in its directory without
asking. Claim it with `register_files` where the files are your plugin's data rather
than the reader's notes — `plugins/vocab` does, so nothing but its own tools reaches the
word lists. A plugin declares the contract it was written against with `CONTRACT`, and
cora offers 2.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · SQLite with sqlite-vec · sentence-transformers · React over Starlette,
and a Telegram bot beside it.
Gates: ruff, ty and pytest on the Python, eslint, tsc and vitest on the page, and a
browser tier nothing runs for you.
