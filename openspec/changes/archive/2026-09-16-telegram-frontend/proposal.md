## Why

cora can only be reached from a page on the machine that runs it, so nobody asks it
anything while away from that machine.

## What Changes

- A second frontend ships: a Telegram bot over the same assembled app, beside the page.
- The one-frontend rule becomes a rule every frontend is held to, rather than a count.
- A chat is a conversation — its id is the thread the turn runs on, so history is kept.
- A turn that stops to ask puts its card in the chat, its ways off numbered.
- A reply naming one of those numbers finishes the turn, and anything else is told so.
- Only allow-listed chats are answered, and a bot allow-listing nobody refuses to start.
- One documented command starts the bot, as one already starts the page.
- Out of this change: streaming, uploads, plugin management, scope pinning, group chats.

## Impact

- `frontends/telegram/` — a new workspace member: the bot, its long poll, its command
- `pyproject.toml` — the member, its workspace source, its dev dependency, its src root
- `Makefile`, `README.md`, `mkdocs.yml`, `docs/how-to/get-started.md` — the second
  command to run, and where it is written down
- `docs/how-to/run-the-telegram-bot.md` — the page that command points at
- `docs/index.md`, `docs/the-page.md`, `docs/big-picture.md` — each said cora had one
  frontend, in its own words
- `docs/privacy-and-ethics.md` — a second host answers now, and the page lists hosts
- `openspec/specs/frontend/spec.md` — the requirement that counted frontends instead of
  holding them to something, and the purpose above it
- `docs/assets/component-map.svg` — redrawn, because the map reads the frontends it ships
- `tests/guards/`, `tests/helpers/workspace.py` — the guards read every frontend rather
  than the one they named
- Leaves alone: the domain, the ports, the engine, the adapters, the composition root,
  every plugin, and the React frontend
