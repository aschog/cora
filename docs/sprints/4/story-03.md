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
citation numbering it enables. Both landed; `Turn` and `thread_to_turns` retired with the
history parameter that was their only caller.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.
**(migrated)** marks a test that moves rather than a new one.

#### The outer test (`tests/test_memory.py`)

- [x] **(int)** a session where the user shares a fact ends with the model calling
      `remember`; a fresh session over the same memory file briefs the model with that
      fact, and the sidebar lists it — the `xfail` came off when half one landed
- [x] **(int)** clearing from the sidebar empties the panel and the store alike, and the
      next turn's brief carries nothing

#### The `Memory` port and its fake (`ports/memory.py`, `tests/fakes.py`)

- [x] the fake recalls remembered facts oldest first, each under a stable key
- [x] forgetting a key removes that fact alone; clearing removes them all

#### The sqlite adapter (over LangGraph's `SqliteStore`)

- [x] a remembered fact is recalled by a new adapter over the same file — the reopen in
      miniature
- [x] forget and clear behave as the fake does, against the file
- [x] facts live under the user's namespace — another user id recalls nothing
- [x] a fresh path's directories are created, and opening the same file twice is harmless
- [x] a broken database surfaces as `AdapterError`, so the friendly-failure path holds

#### The remember tool (`engine/`, beside the search tool)

- [x] the tool stores the model's `fact` through the port and confirms in words the model
      can relay
- [x] dispatched through `ToolRuntime`, a call with no `fact` comes back an
      invalid-arguments tool error
- [x] a fact remembered through the runtime reaches the port intact

#### Recall reaches the model (`PrepareStep`)

- [x] the turn's brief carries every remembered fact beneath the plugin prompt
- [x] nothing remembered → no memory section in the brief
- [x] the rules tell the model to call `remember` **only when the user asks** — never on
      its own judgement, so a kept fact is one the user asked for

#### The thread owns the conversation

- [x] `LangGraphRunner.run` carries a thread id — a second run on the same thread starts
      from the first run's state
- [x] two thread ids share nothing
- [x] `PrepareStep` appends the validated question alone; the brief lives in its own
      per-turn key, so a ten-turn thread holds one brief, not ten
- [x] `PrepareStep` opens the turn: stale `answer`, `answer_in_hand` and `reconsidered`
      cleared, and `turn_start` recorded — the round baseline and the tool-use question
      both read from it. The trace baseline is *not* in the state: a per-turn key is
      stale on the pre-turn state a thread yields first, which is the one state the
      baseline has to be taken from
- [x] a previous turn reaches the model as its user and assistant words only — tool
      messages, tool-call stubs and grounding reminders stay in the thread *(migrated)*
- [x] previous turns are capped at `max_history_turns`; the current turn is never cut
      *(migrated: cap, shorter, exact, odd, zero)*
- [x] `ModelStep` sends brief + view, never the raw transcript
- [x] the round budget is the turn's, not the conversation's — a new turn starts fresh —
      and `rounds` leaves the state altogether: a turn's model calls are counted off its
      own slice of the transcript, so there is no counter to reset or carry over
- [x] an empty final answer does not circle the gate forever — "the gate has looked" and
      "the gate is holding something" become two keys, because clearing the held answer
      each turn left presence unable to tell them apart
- [x] a search made last turn is not this turn's tool use, so the grounding gate still
      gets its look
- [x] `Agent.answer` takes the thread id and seeds only the question — `history` leaves
      the signature *(migrated)*
- [x] `on_step` and `ChatResult.trace` report this turn's steps alone, not the replayed
      thread's
- [x] `ChatResult.sources` resolve against the whole conversation's registry

#### Citations become per-conversation

- [x] a second turn's retrieval continues the numbering — a new document gets the next
      number, not `[1]`
- [x] a source retrieved again next turn keeps its number
- [x] an answer echoing last turn's `[1]` resolves to last turn's source

#### ⇄ Switchover (`assemble`, config, UI)

- [x] `assemble` offers `remember` beside `search_documents` and the runtime dispatches it
- [x] a plugin tool named `remember` is rejected at assembly, like `search_documents`
- [x] `assemble(memory=…)` reaches both the tool and the recall — behavioural
- [x] `App` exposes `memory`, so the sidebar has a port and no adapter
- [x] `Config` reads `CORA_MEMORY_PATH`, default beside the chroma default
- [x] the chat passes a per-session thread id and no history — `thread_to_turns` retires
      *(migrated)*
- [x] **(int)** the sidebar lists each remembered fact
- [x] **(int)** a fact's delete button removes just that fact
- [x] **(int)** clear-all empties the panel, and a rerun keeps it empty
- [x] **(int)** a memory that cannot be reached says so and leaves the chat alone —
      the panel is a sidebar, not the app
- [x] **(int)** an app assembled with no memory shows no panel, is offered no
      `remember`, and is told no rule about it: the absence is visible, not silent

#### Found by the branch review

- [x] a fact carrying an instruction is refused before it is stored, and an ordinary one
      passes — the model writes the fact, so the question's validation never saw it, and
      a stored instruction would open every future session
- [x] the recalled block says of itself that it is notes and not rules, stated after
      them — the treatment retrieved passages already get
- [x] a fact longer than the bound is refused; memory was the one prompt-visible thing
      with no cap of its own
- [x] a fact already known is not kept twice
- [x] a plugin's own rules do not police what is remembered — the shipped medical filter
      would make "remember I have diabetes" unkeepable and close nothing
- [x] `clear` removes more facts than one page holds — it read one page and deleted what
      it had read, so "forget everything" left the rest and the panel repopulated
- [x] `recall` returns the newest facts when there are more than it shows, ordered by the
      adapter's own key: the store's timestamp ties at one second, so the window used to
      be whatever the query planner yielded — in practice the oldest, which the user
      could not delete because it was the newest that were hidden
- [x] a forgotten fact brings a hidden one back into view
- [x] **(int)** a write that cannot reach the store says so and keeps the chat — only the
      read path was guarded, so a delete crashed the page with a traceback
- [x] a memory that cannot be read costs the brief its facts, not the turn, and is traced
      as a failed step
- [x] a store that cannot be written refuses rather than ending the turn
- [x] the gate fires again on a later turn of the same thread — `reconsidered` left
      behind would silence it for the life of the thread, and the whole suite passed
      without the reset
- [x] an answer belongs to the turn that asked for it
- [x] the first state a runner yields is the thread as the turn found it — the promise
      `Agent` builds its per-turn slice on, pinned where it is made
- [x] a second turn round-trips every type the state carries, against an explicit
      checkpoint allowlist: LangGraph deserialises unregistered types with a logged
      warning it says will become a block, and a logger warning is invisible to a suite

#### Close

- [x] **(llm)** a real model calls `remember` when told "I'm vegetarian — keep that in
      mind" and, on a fresh thread, folds it into a food-adjacent answer unprompted
- [x] **(llm)** the acceptance run redirects the memory file as well as the document
      store — an acceptance test that remembered things wrote into the developer's own
