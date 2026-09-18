# Get started

Having it running. What cora *is* is the [front door](../index.md).

## Install

Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22 — the page is built from
source — and an [OpenRouter key](https://openrouter.ai/keys):

<!-- --8<-- [start:install] -->
```sh
uv sync                                    # install the environment
npm ci --prefix frontends/react/ui         # and the page's
git config core.hooksPath .githooks        # enable pre-commit + commit-msg hooks
```
<!-- --8<-- [end:install] -->

## Load the plugins

A bare cora answers, and loads nothing it was not given. This repository's four go in
by dropping them in the folder — linked, so an edit is live:

<!-- --8<-- [start:plugins] -->
```sh
mkdir -p .cora/plugins
for each in security fitness interview travel; do
  ln -s "$(pwd)"/plugins/$each/src/cora/plugins/$each .cora/plugins/$each
done
```
<!-- --8<-- [end:plugins] -->

- That makes it a coach, an interview partner and a travel companion, with a
  prompt-injection screen over all three. Remove a link to see what the box does
  without it.
- The fields come with them: `fitness`, `interview` and `travel` are offered because
  those three register them. `CORA_SCOPES` is for a field *no* plugin brings, which is how a field
  holding only documents exists: `CORA_SCOPES=notes`.
- The rest of what the folder does: [load plugins](load-plugins.md).

## Run

<!-- --8<-- [start:run] -->
```sh
export OPENROUTER_API_KEY=sk-or-...
make run                                   # or: make run-env, to read the key from .env
```
<!-- --8<-- [end:run] -->

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000`; `make run-env` reads `.env` as well as the shell it was started
from, and a variable already exported there wins over the file.

`make bot` runs the same app in a chat instead of a browser — two settings of its own,
and [a page about them](run-the-telegram-bot.md).

## Gates

```sh
uv run ptw .      # test watch mode (unit tier, reruns on save)
uv run pytest     # unit tests — the tier the hook runs
uv run ruff format . && uv run ruff check . && uv run ty check
```

The hook runs those on commit and CI on every push; messages follow
[Conventional Commits](https://www.conventionalcommits.org).

```sh
npm --prefix frontends/react/ui run lint    # eslint, plus what it cannot see
npx --prefix frontends/react/ui tsc -b      # type check
npm --prefix frontends/react/ui test        # unit tier, happy-dom
```

CI runs the page's three and the hook does not: they need Node, and a commit touching
no TypeScript should not wait for it.

`make e2e` drives cora through a real browser against a real server, with
`scripts/fake_model_service.py` standing in for the provider — so a run costs nothing
and says the same thing every time. `make e2e-live` runs its one live spec against the
model a deployment answers from, reading the key from `.env`. Local only: they want a
browser, and nothing runs them for you.

It covers a question answered and cited, a document uploaded and deleted, the card a turn
stops on, the gate an effect waits at, a conversation pinned to a field, and a
conversation and a fact deleted from the rails.

## The fitness field's watch

The fitness trainer can be started and finished from an Amazfit watch: one screen added
to a sport in the watch's own workout app, which writes the field's
[notice](../the-page.md#a-fields-notice) when it opens and when its control is tapped.
The trainer follows that notice — the workout's clock starts when the wrist does, and a
tap saves the workout into the field without the page being touched.

```sh
npm i -g @zeppos/zeus-cli      # once
make watch                     # prints a QR code; scan it in Zepp with developer mode on
```

The address is baked in, a watch having no settings screen to type one into, and it is
this machine's name on the network rather than loopback — the phone is what does the
HTTP. Override either end with `make watch CORA_AT=http://host:8000 WATCH_FIELD=fitness`.

**Cora has to be reachable from the phone**, which means `CORA_HOST=0.0.0.0 make run` —
and that puts every route on that network, not the notice alone. On a network you do not
trust, leave the watch off.

The end of a workout reaches nothing: a Zepp OS workout extension is torn down without
its last message getting to the phone, so finishing is a tap on that screen rather than
something the watch notices. Ending the workout itself stays what it always was, on the
watch, and Zepp keeps its own record of the session whatever the page did.

## The packages

The repository root is the app: a `uv` workspace sharing the `cora` namespace. Install
`cora` to use it, add a package to extend it — a plugin or a frontend.
[Where the boundary is drawn](../big-picture.md#the-map).
