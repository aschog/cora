# Feature Plan: Conversation memory

> **Source** `docs/manual-test-findings.md` finding 1 (high) · **Branch** `feature/conversation-memory` · **Builds on** UI error handling (findings 2/3/9), merged
>
> Design spec (brainstorming) + TDD checklist. First branch since the shell
> rewrite to change `cora.core`.

---

## Requirements

- **The model sees prior turns.** `ChatEngine.answer` builds `[system, user]`
  fresh per call, so the app asks "what do you weigh?" and is structurally
  unable to hear the answer. Acceptance: "I weigh 80 kg" → "What did I say my
  weight was?" answers correctly.
- **Failed turns are not sent.** A question blocked by a validation rule never
  reaches the model — otherwise it sees an unanswered question in the
  transcript and may answer it next turn, defeating the rule that blocked it.
- **Bounded context.** Send the last N exchanges, configurable like
  `CORA_TOP_K`; long conversations forget the oldest turns rather than growing
  cost without limit or hitting the model's window.
- **No shared state.** `streamlit_app.py` caches one `App` for every browser
  session (`@st.cache_resource`) and `ChatEngine` is frozen, so the transcript
  cannot live in the engine — one user's memory would be everyone's.

---

## Design (architecture level)

`<<existing>>` = reused unchanged.

- **`Turn`** (`cora.core.turn`) — frozen `{role, text}`, a root value object
  beside `chunk.py`. What the UI hands inward: plain conversational facts, not
  the chat-model port's vocabulary. The engine owns the translation into
  `Message`, so tool-call plumbing never reaches the shell.
- **`ChatEngine.answer(user_input, history=())`** — the only signature change.
  Validation and retrieval still see the current question alone; the history
  lands between the system prompt and the current user message in
  `_initial_messages`. Defaulting to `()` keeps every existing caller and test
  valid, and keeps the engine a pure function of its arguments.
- **Truncation in the engine** — a `max_history_turns` field, fed from a new
  `CORA_HISTORY_TURNS`. Prompt assembly is the engine's job, so the cap belongs
  next to it rather than in the caller.
- **UI derives, does not store** — a pure helper maps the existing
  `session_state.messages` to `Turn`s, skipping error entries. One source of
  truth, no second transcript to drift, and the "failed turns are not sent"
  rule is one filter in framework-free code.

```mermaid
---
title: One answered turn, with memory
---
sequenceDiagram
  actor user
  participant ui as ui : Streamlit shell
  participant engine as engine : ChatEngine
  participant model as model : ChatModel

  user->>ui: question
  Note over ui: map thread to turns, skip error entries
  ui->>engine: answer(question, history)
  Note over engine: validate and retrieve on the question alone
  engine->>model: system + last N turns + question
  model-->>engine: answer
  engine-->>ui: ChatResult
  ui-->>user: answer, appended to the thread
```

---

## Testing (§8 tiers)

Unit tier carries this feature — the engine is pure and the mapper is
framework-free, so both test without `AppTest`. `ScriptedChatModel`
`<<existing>>` already records `last_messages`, which is the assertion surface
for what the model received. One integration test for the acceptance case.

---

## TDD checklist (red → green → refactor; commit per green)

Core

- [ ] `Turn(role, text)` is frozen; `answer` accepts `history` and places it
      between the system prompt and the current question (assert on
      `ScriptedChatModel.last_messages`).
- [ ] `answer` with no history sends exactly what it sends today — the
      default keeps existing behaviour bit-for-bit.
- [ ] history longer than `max_history_turns` is truncated to the most recent
      turns, oldest dropped first.
- [ ] retrieval and validation still receive the current question alone, not
      the history (guards the "don't poison the query" decision).

Composition

- [ ] `Config` exposes `CORA_HISTORY_TURNS` with a default; `assemble` passes
      it to `ChatEngine`.

UI

- [ ] the thread-to-turns mapper skips error entries, keeps user/assistant
      pairs in order, and maps an empty thread to `()`.
- [ ] acceptance (`AppTest`): state a fact, then ask about it, and the second
      call receives the first exchange.

Docs

- [ ] README: `CORA_HISTORY_TURNS` alongside the other `CORA_*` overrides.

---

## Open questions / risks

- **Retrieval is still single-turn.** "What about for women?" carries the
  conversation but retrieves on those five words alone, so the *documents*
  will not follow the thread. Fixing it means query rewriting — a second model
  call and its own feature. Logged, not smuggled in; expect it to be the first
  "memory still feels broken" report.
- **`Turn` vs `Message` look alike.** Accepted duplication: a `Message` is one
  round-trip's plumbing, a `Turn` is a conversational fact that outlives it and
  gets counted and truncated. Revisit if they stay identical once tool calls
  are involved.
- **Thread as source of truth.** Deriving history from render state means any
  future entry variant must be classified as conversational or not. The
  alternative — a parallel transcript — trades that for drift.

---

## Verification (end-to-end)

- `uv run pytest` and `uv run pytest -m integration` green; gates clean.
- Manual (real key, headless over the real `streamlit_app.py`): the finding's
  own transcript — "I weigh 80 kg. Remember that." then "What did I just tell
  you my weight was?" — plus a rejected question followed by a normal one, to
  confirm the refusal never reaches the model.
