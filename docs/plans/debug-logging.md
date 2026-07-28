# Feature Plan: Debug-Logging Seam at the Ports

> **Branch** `feature/debug-logging` · **Builds on** chat engine + Streamlit UI (done)
> · Touches `cora.app` (config, assembly) and one new module in `cora.adapters`; core, plugins, UI untouched.

---

## Requirements

- New env flag `CORA_DEBUG` (default off) surfaced as `Config.debug: bool` via `Config.from_env`.
- When on, one concise stdlib-`logging` line per port call, visible in the terminal running Streamlit:
  - `ChatModel.complete()` — message count + roles, truncated content; reply: requested tool calls + truncated text.
  - `Retriever.query()` — k, returned chunk sources + scores; `add()` — chunk count + file source; `sources()`/`contains()` delegate silently.
  - `Embedder.embed()` — number of texts embedded.
- Truncation bounds every logged field — no full documents/prompts flooding the terminal; secrets never logged (the API key never crosses a port).
- When off: zero behavior change, no logging config touched.
- Unit tier: existing in-memory fakes + pytest `caplog`; no network, models, or UI.

---

## Design (architecture level)

- **Pattern: Decorator (GoF) over the three port Protocols.** One new adapter module (`cora.adapters.port_logging`) with three thin wrappers — logging chat model, retriever, embedder — each holding an inner port, delegating every method unchanged, and emitting one DEBUG line per call on a logger in the `cora` namespace. Structural Protocol conformance is verified by ty (house rule: no conformance tests).
- **Placement — adapters layer.** The wrappers *are* port implementations, peers of the Chroma/OpenRouter/sentence-transformers adapters. Core stays observability-free; dependency rule UI → Core ← Plugins holds unchanged (core imports nothing new; app already imports adapters).
- **Shared truncation helper** (pure function, same module): caps any logged text with an ellipsis marker, one cap constant. This is the flood/secrecy guard — wrappers only ever see port-call arguments, and `Config.api_key` is not among them.
- **Composition root decides** (`assembly.py`): `assemble` gains a `debug` flag (default off); when true, the three ports are wrapped before service wiring — unit-testable with fakes. `build` forwards `config.debug` and, when on, enables DEBUG level + a stream handler on the `cora` logger via a small idempotent helper. Namespace-scoped: the root logger is never touched; when off, no logging call happens at all.
- **Config**: `from_env` parses `CORA_DEBUG` following the existing pattern (a `_bool` beside `_int`; "1"/"true" truthy, absent → False).
- **Runtime flow change: none in the core.** With debug on, every core→port call passes through a wrapper that logs and delegates; fakes, real adapters, and services are all unaware.

### Trade-offs / rejected alternatives

- **Logging inside each real adapter** — rejected: triplicates the concern, mixes provider-translation code with observability, leaves fake-wired runs unlogged.
- **Logging in core services (engine/KB)** — rejected: operational concern inside the domain; the port seam is exactly where "what crossed the boundary" is observable.
- **Observer/event port for telemetry** — rejected: an abstraction with one consumer; plain decorators earn their place, an event bus doesn't (simplicity first). The progress-callback seam stays separate.
- **One generic reflective proxy** — rejected: loses ty-verifiable typing and per-method message tailoring; three explicit wrappers cost about the same.
- **`logging.basicConfig`** — rejected: hijacks the hosting process's root logger; configure only the `cora` logger, only when the flag is on.

---

## TDD checklist (red → green → refactor; commit per green; bottom-up)

Config

- [x] test that `Config.from_env` sets `debug=False` when `CORA_DEBUG` is unset.
- [x] test that `CORA_DEBUG=1` / `true` (case-insensitive) set `debug=True`; `0` / `false` stay off.

Truncation helper

- [x] test that text over the cap is truncated with a marker; short text passes unchanged.

Wrappers (fakes + caplog)

- [x] test that the logging chat model returns the inner fake's reply and passes messages/tools through unchanged.
- [x] test that a `complete` call logs one line with message count + roles + truncated content.
- [x] test that the reply side logs requested tool-call names and truncated reply text.
- [x] test that a marker buried deep in a long prompt never appears in any log line (every field bounded).
- [x] test that the roles field stays bounded for a long history (discovered: `", ".join(roles)` grew with turn count, so the request line was not bounded end to end).
- [x] test that the logging retriever's `query` delegates and logs k plus returned chunk sources + scores.
- [x] test that its `add` delegates and logs chunk count + file source.
- [x] test that an `add` with no chunks logs `0 chunks` instead of raising (discovered: reading `chunks[0].source` made the debug wrapper crash on an empty batch).
- [x] test that `sources()` and `contains()` delegate transparently.
- [x] test that the logging embedder delegates and logs the number of texts embedded.

Wiring

- [x] test that the log-config helper enables DEBUG + a handler on the `cora` logger when on, is idempotent, and does nothing when off (root logger untouched).
- [x] test that `assemble(..., debug=True)` yields an app whose single chat turn emits chat-model, retriever, and embedder records; default `assemble` emits none.
- [x] test that `build` forwards `config.debug` and triggers log configuration only when set (integration tier, matching the existing `build` test style).

---

## Acceptance (manual)

Verified headlessly on 2026-07-28 over the real stack — real embedding model,
real Chroma store, real fitness plugin, the Streamlit page driven through
`AppTest` (upload → chat turn). Only the LLM was scripted, so a tool-call round
could be forced without spending a live key.

- [x] `CORA_DEBUG=1`: upload a doc → terminal shows an embed-count line and an `add()` line; one chat turn → embed line, `query()` line with sources + scores, `complete()` lines including a tool-call round; all content visibly truncated; API key nowhere in the output. Observed, in order: `embedded: 2 texts`, `indexed: 2 chunks from protein_guide.md`, `embedded: 1 texts`, `retrieval: k=5, 4 hits [energy_balance.md#0 0.43, protein.md#0 0.22, …]`, `chat request: 2 messages [system, user]`, `chat reply: tool calls [calculate_daily_energy]`, `chat request: 4 messages [system, user, assistant, tool], last: {"bmr": 1780.0, "tdee": 2759.0}`, `chat reply: tool calls [], text: Your maintenance is about 2600 kcal…`. Longest line 154 chars; a marker buried in the uploaded document and the API key both appear zero times in stdout and stderr.
- [x] Without the flag: zero `cora` log lines, same answer in the UI, no exceptions.
- [x] Gates green: `uv run ruff format --check`, `uv run ruff check`, `uv run ty`, `uv run pytest` (283 unit) and `uv run pytest -m integration` (20).
