## Context

cora runs on one machine and is reached only from the page that machine serves (see
proposal.md — Why).

## Goals / Non-Goals

**Goals:**

- A second frontend that adds nothing to the core — the app it drives is the one the
  page drives.
- A rule about frontends that the next one also passes, rather than a count of one.
- What is rendered into a chat is a value, testable without a network.
- The bot holds no state a restart would lose.

**Non-Goals:**

- Streaming, uploads, plugin management, scope pinning, group chats, inline keyboards.
- A hosted deployment: the bot polls out from the machine, and nothing dials in.
- Editing a card's values from the chat, which the numbered ways off do without.

## Decisions

- **The seam is `App`, already the frontend contract**: `agent.answer`, `agent.resume`,
  `agent.pending`, read off a composition the frontend did not build.
- `frontends/telegram` is a workspace member beside `frontends/react`, contributing
  `cora.frontends.telegram` to the namespace the build backend leaves open.
- Nothing under `src/` changes, so the change needs no general core work ahead of it.
- **The Bot API is called over HTTPS directly, long-polling `getUpdates`.** Two
  endpoints and a poll loop are less code than the wiring a bot framework asks for.
- Rejected: `python-telegram-bot`, an async handler framework over an agent whose turn
  is a blocking call — the impedance costs more than it saves at this size.
- Rejected: webhooks, which want a public URL and an inbound port on a laptop.
- **A result and a card each render through a pure function**, mirroring the page's
  `payloads`, and a failure is the sentence the loop picks where it catches it.
- The tests drive the loop against a hand-written fake of the two calls, and the pure
  functions directly — the network is the only stub, as the house rule asks.
- **The open card is read from `agent.pending`, never held in the bot.** A restarted bot
  still knows the chat is parked, and no second store appears.
- The ways off are numbered off the card each time it is read, so the number a reply
  names is a position in what was just sent.
- An action gated on a value the chat cannot write is dropped before numbering, because
  a card always keeps one way off that stands as it is.
- **One update is handled at a time, in the order they arrive.** A turn runs for a
  minute, so a second chat waits behind the first — noted as a ceiling, not hidden.
- **The allowlist is checked before a turn is run, and the poll advances either way.**
  A chat nobody named cannot park the bot behind its own message.
- Token and allowed chats are read from the environment and refused with the app's own
  `ConfigurationError`, so a deployment missing either is refused at start.
- An answer over Telegram's message ceiling is sent in parts rather than dropped by the
  API, which is what the "answer arrives in the chat" requirement means at length.
- The ceiling is counted in the code units Telegram counts, not in characters, because
  an emoji is one of those and two of these.
- **A refused call is redacted before it propagates.** The token is in the URL, and the
  client puts that URL in what it raises.
- A reader who blocked the bot and a rate the API asks us to wait out are the adapter's
  to absorb, because neither is news the loop could act on.

## Risks / Trade-offs

- One chat at a time is a real ceiling → a thread per chat is the upgrade, and the
  rendering function does not change when it arrives.
- A long poll that drops mid-flight would end the process → the loop waits and polls
  again, and only a refused start exits.
- Numbering by position means a card re-sent with different actions renumbers → the
  reply is checked against the card that is open now, not the one that was drawn.
- The bot token reaching a log would hand over the chat → it is read from the
  environment and never rendered, as every other secret is.
- A frontend that nobody is watching answers while unattended → the allowlist is the
  trust boundary, and an empty one refuses rather than defaults to open.
- The offset is held in memory and only sent on the next poll → a crash mid-turn leaves
  the batch unconfirmed, so a restarted bot answers those messages again.

## Migration Plan

Nothing changes for the page: it serves the same app from the same process, started by
the same command. The bot is a second command, run or not run.

## Diagrams and guards

- `docs/assets/component-map.svg` is redrawn: the map reads the frontends the workspace
  ships, so a second one belongs in it and the diagram guard fails until it is.
- The packaging guard sees a second member, and the docs guard sees the command that
  starts it.
- The architecture guard gains the entry a new portion asks for: the bot may bind the
  HTTP client it polls with, and nothing else.
