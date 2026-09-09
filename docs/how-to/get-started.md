# Get started

Install it, run it, load plugins into it, and run the gates it is held to. What cora
*is* is the [front door](../index.md); this is the page for having it running.

## Install and run

Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 — the page is built from
source — and an [OpenRouter key](https://openrouter.ai/keys):

<!-- --8<-- [start:install] -->
```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
```
<!-- --8<-- [end:install] -->

<!-- --8<-- [start:run] -->
```sh
export OPENROUTER_API_KEY=sk-or-...
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness,cora.plugins.travel
export CORA_SCOPES=fitness,travel
make run                                   # or: make run-env, to read the key from .env
```
<!-- --8<-- [end:run] -->

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000`. The target exists so the command survives the next time a package
moves — the module it names is one line, in the `Makefile`. `make run-env` is the same
thing reading its environment from `.env`, so the exports above go in that file
instead. cora loads no plugin unless asked, so the `CORA_PLUGINS` line is what turns
this from a bare cora into the coaching app with a prompt-injection screen. A field is
offered because something brings it: the coaching persona and its calculators bring
`fitness`, the travel persona and its notes bring `travel`, while the medical filter and
the injection screen are system-wide and hold whatever a turn is running as. So the
`CORA_SCOPES` line above is optional — it names fields *beyond* what the plugins
register, which is how a field holding only documents exists.

## Loading plugins

A plugin does not have to be installed. Drop a single `.py` file into `./.cora/plugins/`
and cora loads it with no packaging at all, named for the file. A plugin that has grown
past one file goes in the same way: drop its folder — a directory holding `__init__.py` —
and it is one plugin named for the folder, its own relative imports working as written.
The folder is read in name order after the modules `CORA_PLUGINS` names, and
`CORA_PLUGINS_PATH` moves it. It is read relative to where cora was started, and
everything in it is code cora runs — `CORA_DEBUG` logs which folder that was. What a
drop-in imports is not installed for it: anything beyond cora and the standard library
has to be in cora's environment already, or the plugin is refused by name.

And the folder is live. A plugin dropped there while cora serves is installed by the
next request — reload the page and it is in the menu — a deleted one is gone the same
way, and an edited one serves its new code. No environment change, no restart. The
field a plugin registers under arrives with it — the picker, the router and the rails
offer it, and it goes when the plugin goes. A symlink counts as its target, so this
repo's own plugins deploy by linking:

```sh
ln -s "$(pwd)"/plugins/travel/src/cora/plugins/travel .cora/plugins/travel
```

One route per plugin, though: a module `CORA_PLUGINS` names and a link (or file) in the
folder are two plugins with one name, which cora refuses — link it *or* name it. A turn
already running finishes on the plugins it started with. A drop that cannot load is
louder: every request is refused, readably and naming the plugin, until the folder
loads again — fix or remove the file and the prior set serves on, nothing lost. Only
the folder is live: what `CORA_PLUGINS` names is fixed at start.
`make plugins` prints what loaded: every plugin under where it came from, with its tools,
its instructions and the points in a turn it subscribed to, and anything registered
without a scope marked `system-wide`. `GET /api/plugins` carries the same listing. A
plugin declares which version of the contract it wants, and one cora does not offer is
refused before its `extend` is called.

`make plugins` prints what loaded, and `GET /api/plugins` carries the same listing.

## What a plugin reads as its settings

A plugin reads its own settings from the environment, under its own name:
`CORA_PLUGIN_TRAVEL_SERPAPI_KEY` reaches `cora.plugins.travel` as `serpapi_key`, which
is the one setting a shipped plugin takes. Cora's own `CORA_` variables are a separate
namespace, so no plugin can read them, and cora reads the environment so a plugin does
not have to.

## The packages

The app is the repository root; a `uv` workspace sharing the `cora` namespace. You install
`cora` to use it and add a package to extend it — a plugin or a frontend. Where the
boundary is drawn: [`docs/big-picture.md`](../big-picture.md#the-map).

## Gates

```sh
uv run ptw .      # test watch mode (unit tier, reruns on save)
uv run pytest     # unit tests — the tier the hook runs
uv run ruff format . && uv run ruff check . && uv run ty check
```

The hook runs those four on commit and CI runs them on every push; commit messages
follow [Conventional Commits](https://www.conventionalcommits.org).

The page has its own three, which CI runs and the hook does not — they need Node, and a
commit that touches no TypeScript should not wait for it:

```sh
npm --prefix frontends/react/ui run lint    # eslint, plus what it cannot see
npx --prefix frontends/react/ui tsc -b      # type check
npm --prefix frontends/react/ui test        # unit tier, happy-dom
```

And one more that nothing runs for you. `make e2e` drives cora through a real browser
against a real server — the real page, the real API, the real stores, the real turn —
with `scripts/fake_model_service.py` standing in for the provider, so a run costs
nothing and says the same thing every time. It covers a question answered and cited, a
document uploaded and deleted, the card a turn stops on, the gate an effect waits at,
a conversation pinned to a field, and a conversation and a fact deleted from the rails.
`make e2e-live` runs its one live spec against the model a deployment actually answers
from, reading the key from `.env`. Local only: it wants a browser, and CI has enough to
say about a push already.
