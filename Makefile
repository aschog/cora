# Shortcuts for the commands whose paths are long enough to get retyped wrong. Everything
# here is a thin wrapper over `uv run` — the real definitions are in pyproject.toml.

REACT := cora.frontends.react.server
TELEGRAM := cora.frontends.telegram.server

.PHONY: run run-env run-watch bot bot-env plugins plugins-env ui ui-build ui-test e2e e2e-store e2e-live docs docs-serve diagram watch

# cora, as one process serving the page and the API on 127.0.0.1:8000. It builds first
# because the server only ever reads `ui/dist` — without that a source change is
# invisible on the page. Reads OPENROUTER_API_KEY from the environment.
run: ui-build
	uv run python -m $(REACT)

# Reads it from .env instead, which is how the live tier is run too.
run-env: ui-build
	uv run --env-file .env python -m $(REACT)

# The same, for a session the watch takes part in. Two things differ and both are about
# a device that is not this machine: the phone does the watch's HTTP, so cora listens on
# the network rather than on loopback alone — which puts every route there, so run it on
# a network you trust — and the machine has to stay up while the lifter is not touching
# it, which `caffeinate` is. Where there is no `caffeinate` the run is the same run.
KEEP_AWAKE := $(shell command -v caffeinate 2>/dev/null)

run-watch: ui-build
	CORA_HOST=0.0.0.0 $(KEEP_AWAKE) $(if $(KEEP_AWAKE),-i,) uv run --env-file .env python -m $(REACT)

# cora in a Telegram chat, for the machine you are not sitting at. The bot polls out,
# so nothing has to reach in. Reads CORA_TELEGRAM_TOKEN and CORA_TELEGRAM_CHATS beside
# OPENROUTER_API_KEY, and refuses to start without either of the two.
bot:
	uv run python -m $(TELEGRAM)

# The same, reading its environment from .env — as `run-env` is to `run`.
bot-env:
	uv run --env-file .env python -m $(TELEGRAM)

# What this deployment loaded, and what each plugin registered. It assembles the app the
# environment describes rather than reading the manifests, so what prints is what runs.
plugins:
	uv run python -m cora.app.listing

# The same, reading its environment from .env — as `run-env` is to `run`.
plugins-env:
	uv run --env-file .env python -m cora.app.listing

# The page on its own, for working on it: Vite on 5173, proxying /api to `make run`.
ui:
	cd frontends/react/ui && npm run dev

ui-build:
	cd frontends/react/ui && npm run build

ui-test:
	cd frontends/react/ui && npm test

# The browser suite: cora driven through chromium against a real server. The store is
# laid out fresh each run — a suite that deletes a document and a conversation has to
# start from the same place every time. The fixture plugins are copied rather than
# linked, because one of the things a deployment can do to a dropped plugin is delete
# it; the shipped fitness plugin is linked instead, so the browser tier runs the page
# that ships rather than a copy of it — a delete unlinks what it finds, so the tree is
# safe from the suite either way.
# Playwright starts the servers itself and stops them again; `playwright.config.ts` says
# which. Local only: it needs a browser, and CI has enough to say about a push already.
E2E_STORE := .cora/e2e

e2e-store:
	rm -rf $(E2E_STORE)
	mkdir -p $(E2E_STORE)/plugins
	cp -R tests/e2e/plugins/. $(E2E_STORE)/plugins/
	ln -s $(CURDIR)/plugins/fitness/src/cora/plugins/fitness $(E2E_STORE)/plugins/fitness
	ln -s $(CURDIR)/plugins/vocab/src/cora/plugins/vocab $(E2E_STORE)/plugins/vocab

e2e: ui-build e2e-store
	cd frontends/react/ui && npx playwright test

# The same suite's one live spec, against the model a deployment actually answers from.
# Reads the key from .env, like every other live tier, and is run by hand before a
# submission rather than on a schedule.
e2e-live: ui-build e2e-store
	set -a; . ./.env; set +a; cd frontends/react/ui && CORA_E2E_LIVE=1 npx playwright test

# MkDocs has forked: its owner is publishing a v2 that drops the plugin system, and
# `properdocs` is a continuation of 1.x that arrives here transitively. Both sides warn on
# every build, in opposite directions, and each reads its own variable. We stay on
# mkdocs 1.6.1, pinned by uv.lock, and say so once here instead of in every log.
QUIET_FORK := NO_MKDOCS_2_WARNING=true DISABLE_MKDOCS_2_WARNING=true

# The docs site — the written pages and a reference generated from the source.
# `mkdocs.yml` configures it; --strict is what the integration tier runs, so a build that
# passes here is the one CI checks.
docs:
	$(QUIET_FORK) uv run mkdocs build --strict

# 8001, because the React shell already wants 8000: reading the docs beside the running
# app must not need one of them stopped. `tests/guards/test_docs_site.py` holds that.
docs-serve:
	$(QUIET_FORK) uv run mkdocs serve --dev-addr 127.0.0.1:8001

# Every drawing in the docs. The component map reads `cora.app.assembly` for what the
# boxes and the connectors are and places them itself — that map has one fixed shape, so
# there is no layout to search for. The domain map is read out of the classes by pyreverse
# and laid out by graphviz, which this target needs installed. The session maps read one
# method each, and the graph off the nodes the runner declares, and space themselves to
# what is said on them. Every SVG is committed, and `tests/guards/test_diagrams.py` reads
# each one for what it contains — never for its bytes, which are the layout of whichever
# graphviz drew it — so a port, a class or a step added without a redraw is a red test.
diagram:
	uv run python scripts/gen_component_map.py
	uv run python scripts/gen_domain_map.py
	uv run python scripts/gen_session_maps.py

# The fitness field's screen for the wrist: one data page added to a sport in the watch's
# own workout app, which writes that field's notice when it opens and when its control is
# tapped. The address is baked in because a watch has no settings screen to type one into
# — and it is this machine's name on the network, not loopback, because the phone is what
# does the HTTP. Override it with `make watch CORA_AT=http://…`, and the device with
# `WATCH_DEVICE=`. The build prints a QR code; scanning it in Zepp with developer mode on
# is the install.
WATCH := plugins/fitness/watch
WATCH_FIELD ?= fitness
WATCH_DEVICE ?= Amazfit Balance
CORA_AT ?= http://$(shell scutil --get LocalHostName 2>/dev/null || hostname -s).local:8000

watch:
	@command -v zeus >/dev/null 2>&1 || { \
	  echo "zeus is not installed. Install it with: npm i -g @zeppos/zeus-cli"; exit 1; }
	@printf "export const NOTICE = '%s'\n" \
	  "$(CORA_AT)/api/scopes/$(WATCH_FIELD)/notice" > $(WATCH)/config.js
	@echo "wrote $(WATCH)/config.js pointing at $(CORA_AT)"
	@cd $(WATCH) && [ -d node_modules ] || npm install --silent
	cd $(WATCH) && zeus preview -t "$(WATCH_DEVICE)"
