# Story 3: It remembers me between sessions

**As a** returning user · **I want** it to keep what I tell it about myself ·
**So that** answers reflect it without me repeating it — and I can see and clear what it
keeps

> **Given** I told it something about myself last session
> **When** I reopen the app and ask a question that depends on it
> **Then** the answer reflects it without me repeating it, and I can see and clear what
> it remembers

Satisfies the medium bonus *long-term / short-term memory in LangGraph*. Closes the
story-1 review's backlog item: citation numbers become per-conversation.

Built in two halves, each mergeable. **First** the store, the tool, the recall and the
sidebar — that alone answers the criterion. **Second** the thread inversion and the
citation numbering it enables. If the second half stalls, the first is the story and the
inversion continues on the branch. The **(llm)** close is optional to the merge.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.
**(migrated)** marks a test that moves rather than a new one.

#### The outer test (`tests/test_memory.py`)

- [ ] **(int)** a session where the user shares a fact ends with the model calling
      `remember`; a fresh session over the same memory file briefs the model with that
      fact, and the sidebar lists it — `xfail(strict=True)` until the slice lands
- [ ] **(int)** clearing from the sidebar empties the panel and the store alike, and the
      next turn's brief carries nothing

#### The `Memory` port and its fake (`ports/memory.py`, `tests/fakes.py`)

- [ ] the fake recalls remembered facts oldest first, each under a stable key
- [ ] forgetting a key removes that fact alone; clearing removes them all

#### The sqlite adapter (over LangGraph's `SqliteStore`)

- [ ] a remembered fact is recalled by a new adapter over the same file — the reopen in
      miniature
- [ ] forget and clear behave as the fake does, against the file
- [ ] facts live under the user's namespace — another user id recalls nothing
- [ ] a fresh path's directories are created, and opening the same file twice is harmless
- [ ] a broken database surfaces as `AdapterError`, so the friendly-failure path holds

#### The remember tool (`engine/`, beside the search tool)

- [ ] the tool stores the model's `fact` through the port and confirms in words the model
      can relay
- [ ] dispatched through `ToolRuntime`, a call with no `fact` comes back an
      invalid-arguments tool error

#### Recall reaches the model (`PrepareStep`)

- [ ] the turn's brief carries every remembered fact beneath the plugin prompt
- [ ] nothing remembered → no memory section in the brief
- [ ] the rules tell the model to call `remember` when the user shares something durable

#### The thread owns the conversation

- [ ] `LangGraphRunner.run` carries a thread id — a second run on the same thread starts
      from the first run's state
- [ ] two thread ids share nothing
- [ ] `PrepareStep` appends the validated question alone; the brief lives in its own
      per-turn key, so a ten-turn thread holds one brief, not ten
- [ ] `PrepareStep` opens the turn: stale `answer` and `answer_in_hand` cleared, the
      turn's trace and round baseline recorded
- [ ] a previous turn reaches the model as its user and assistant words only — tool
      messages, tool-call stubs and grounding reminders stay in the thread *(migrated)*
- [ ] previous turns are capped at `max_history_turns`; the current turn is never cut
      *(migrated: cap, shorter, exact, odd, zero)*
- [ ] `ModelStep` sends brief + view, never the raw transcript
- [ ] the round budget is the turn's, not the conversation's — a new turn starts fresh
- [ ] a search made last turn is not this turn's tool use, so the grounding gate still
      gets its look
- [ ] `Agent.answer` takes the thread id and seeds only the question — `history` leaves
      the signature *(migrated)*
- [ ] `on_step` and `ChatResult.trace` report this turn's steps alone, not the replayed
      thread's
- [ ] `ChatResult.sources` resolve against the whole conversation's registry

#### Citations become per-conversation

- [ ] a second turn's retrieval continues the numbering — a new document gets the next
      number, not `[1]`
- [ ] a source retrieved again next turn keeps its number
- [ ] an answer echoing last turn's `[1]` resolves to last turn's source

#### ⇄ Switchover (`assemble`, config, UI)

- [ ] `assemble` offers `remember` beside `search_documents` and the runtime dispatches it
- [ ] a plugin tool named `remember` is rejected at assembly, like `search_documents`
- [ ] `assemble(memory=…)` reaches both the tool and the recall — behavioural
- [ ] `App` exposes `memory`, so the sidebar has a port and no adapter
- [ ] `Config` reads `CORA_MEMORY_PATH`, default beside the chroma default
- [ ] the chat passes a per-session thread id and no history — `thread_to_turns` retires
      *(migrated)*
- [ ] **(int)** the sidebar lists each remembered fact
- [ ] **(int)** a fact's delete button removes just that fact
- [ ] **(int)** clear-all empties the panel, and a rerun keeps it empty

#### Close

- [ ] **(llm)** a real model calls `remember` when told "I'm vegetarian — keep that in
      mind" and, on a fresh thread, folds it into a food-adjacent answer unprompted
