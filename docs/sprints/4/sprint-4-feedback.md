# Sprint 4 — feedback backlog

The sprint-3 reviewer's findings, plus the open items from
`docs/sprints/3/manual-test-findings.md`, as tracked checklist items. Day-one
artefact per `docs/workflow.md`: feedback gets ticked here, not remembered.

Each item names where it was verified in today's code and how it lands — inside a
sprint-4 story from `docs/sprints/4/spec.md`, or as its own slice.

## Reviewer findings

- [x] **Indirect prompt injection through document text** *(reviewer: biggest issue)* —
      retrieved chunks are concatenated into the system message
      (`core/services/chat_engine.py:107-110`), so an instruction hidden in an uploaded
      document carries the same authority as cora's own rules; the injection rule only
      sees the user's question (`core/services/validation.py`). Move retrieved text into
      a clearly marked user/tool message and label it untrusted data.
      → folded into **story 1**, which puts retrieved text in a `tool` message by
      construction. Fixing it first would mean reworking `ChatEngine`, then deleting that
      code and its tests at the switchover. Story 1 asserts it explicitly: the structure
      comes free, the *untrusted-data label* does not.
      **Done in story 1**: retrieved text now arrives as a `tool` message headed by an
      untrusted-data notice, and a test asserts the document's words never reach the
      system message.

- [ ] **Stronger injection rules as a plugin** — `ValidationPipeline` already runs
      `core_rules + plugin_rules` and a rule is anything with `apply(user_input)`
      (`core/ports/plugin.py:40-41`), but `PromptInjectionRule` is two regexes
      (`core/services/validation.py:7-16`). Carry stronger rules (e.g. LLM Guard) in a
      security plugin. A scan of *document* content hooks at ingest (`add_file`), once per
      file — it is not on the `validate(user_input)` path, and per chunk per turn would be
      a model call per retrieved chunk. Needs plugin composition: `load_plugin` binds
      exactly one (`app/assembly.py:120`).
      → own slice, inside **story 6** (guard rails), with the medical filter. It is defence
      in depth *behind* story 1's fix, not a substitute: a scanner has false negatives,
      message roles do not.
      → **still open, but no longer blocked.** Story 11 made `CORA_PLUGINS` an ordered list,
      so plugin composition is done, and the guard now ships as its own distribution,
      `cora.plugins.security`. What the finding actually asked for has not been built: the
      rule is still the same two regexes
      (`plugins/security/src/cora/plugins/security/injection.py:6-15`), and nothing scans
      document content at ingest. Story 6 was never built, so this needs a story of its own.

- [x] **No grounding or scope decision** — the prompt asks the model to ground its answer
      (`plugins/fitness/__init__.py:10`) but nothing enforces or tests it, so an
      out-of-domain question is answered from model knowledge. Add a tested rule that
      declines unsupported answers, evaluated against in-domain, out-of-domain and
      weak-retrieval cases. Also manual finding #6.
      → own slice, **after story 1**, and story 1 changes nothing here: the instruction
      already ships in the plugin prompt (`plugins/fitness/__init__.py:10`), which is where
      domain policy belongs — a plugin whose tools answer without documents must be able to
      opt out. Enforcement is not unit-sized: against a scripted model the assertion is the
      script, and "in-domain / out-of-domain / weak-retrieval" is the evaluation set below.
      Story 1 also makes retrieval a *decision*, so any rule phrased as "no context →
      refuse" would contradict its second criterion (a greeting is answered without
      retrieving); it has to be scoped to questions the documents were asked to answer.
      **Closed in story 8** (`story-08.md`) and **reopened by story 15** (`story-15.md`):
      the gate that enforced it — a first answer with no search behind it sent back through
      the model once, against a `scope` the plugin named — is gone, because it was the one
      branch of the graph that could not be read and defended. What is left is the
      instruction: `AGENT_RULES` and the fitness plugin's prompt still tell the model to
      search and cite, and the `llm` tier is what can catch a model ignoring them
      (`test_llm_acceptance.py:147,178`).
      → **Decided 2026-08-19: the citation is the grounding evidence, and detection is
      deliberately not built.** A citation cannot be conjured — the numbers come from
      passages the search tool returned, so a clickable `[n]` is text that really is in the
      user's document at those offsets, and a number with no source behind it degrades to
      plain text rather than offering a source that does not exist
      (`frontends/react/ui/src/answer.ts:51-62`). What that does not give is a check that an
      answer *has* citations: an ungrounded answer looks like a legitimately uncited one,
      because cora is meant to answer a question that needs no documents directly. Closing
      that gap costs a gate of the kind story 15 removed for being unreadable, or a
      human-in-the-loop approval step, and neither is worth it against evidence the reader
      can verify by clicking. Raised twice by review; recorded here as a position rather
      than left open a third time.

- [x] **Planner JSON is hand-parsed and fails silently** — `parse_plan` scrapes fences and
      braces, and a parse failure falls back to plain search with no signal
      (`core/services/query_planner.py:22-23,56-77`). Use structured output
      (`with_structured_output` / `response_format` with a JSON Schema) at the adapter
      boundary, and make the fallback observable.
      → own slice, together with the model-adapter item below: both are
      `OpenRouterChatModel`, and structured output widens the `ChatModel` port. Not
      story 1 — the planner is reached only by `advanced`, inside `FusionContextSource`
      (`app/retrieval.py:36-45`); story 1 changes *who calls* the context source, not what
      a mode does inside it.
      → **closes as removed, in story 14**, not fixed: the agent re-searches in the open,
      so the planner and its hand-parsed JSON go rather than get structured output. The
      model-adapter item below stands on its own.

- [x] **Model adapter swallows everything** — every provider exception becomes one generic
      `LlmError` (`adapters/openrouter_chat_model.py:73-77`), with no timeout, no retry
      policy, and `finish_reason`/usage discarded (`to_model_reply`), so a truncated or
      empty completion is treated as a successful answer. Set an explicit timeout and
      retry, preserve error categories, reject empty/truncated finals.
      → own slice, **before story 1** — the agent multiplies model calls per turn.
      → taken on `fix/submission-blockers`, after story 1 rather than before it: the agent
      shipped first, which is why a per-turn multiplier now makes the case rather than
      predicting it. Test list:
  - [x] the client is built with an explicit timeout and a retry count
  - [x] a provider timeout is raised as its own error, worded as "took too long"
  - [x] a rate-limit refusal is raised as its own error, worded as "busy, try shortly"
  - [x] any other provider exception stays the generic `LlmError`
  - [x] a final reply the provider cut off at the token limit is an error, not an answer
  - [x] a final reply with no text and no tool calls is an error, not a blank answer
  - [x] a reply carrying tool calls and no text is untouched — that is how a round starts

- [x] **Medical filter is substring matching** — `MedicalSafetyRule`
      (`plugins/fitness/safety.py:20-25`) refuses any message containing `diabetes`,
      `pregnan`, `blood pressure`…, so "I have diabetes, how should I train?" is blocked
      outright. Distinguish diagnosis/medication requests from training questions that
      can get cautious guidance with a caveat. Also manual finding #7.
      → own slice, inside **story 6** (guard rails).
      → story 6 was never built, so the slice moves to `fix/submission-blockers` on its
      own. The rule stays deterministic and stays ahead of the model — it is what makes
      the refusal cost nothing — but it stops reading a *mention* as a *request*: naming a
      condition is allowed, asking for a diagnosis, a dose or a medication decision is
      not, and the caveat is the plugin's instructions to write. Test list:
  - [x] "I have diabetes, how should I train?" passes the rule
  - [x] "Do I have diabetes?" is still refused
  - [x] "What steroid dosage should I take?" is still refused
  - [x] "Should I stop taking my blood pressure medication?" is refused
  - [x] "Is my pregnancy affecting my macros?" passes — **this replaces a test that
        asserts today's refusal**, because the finding says that refusal is the bug
  - [x] matching stays case-insensitive, asserted on a phrase that still refuses
  - [x] the plugin's instructions tell the model to answer with a caveat and point at a
        professional when a condition is named

- [x] **No streaming** — the port returns a finished reply and the UI blocks on a spinner
      (`core/ports/chat_model.py`, `app/ui/chat.py:93`). Stream through the model
      boundary and render with `st.write_stream`.
      → own slice, after **story 2** (the trace and the stream share the same surface).
      **Done in story 19** (`story-19.md`), through the boundary the finding names rather
      than through Streamlit's renderer: `ChatModel` streams, the graph binds the model node
      to that turn's reader, and `/api/ask` carries a `text` event per piece, so the React
      page grows the answer in place. Streamlit still waits for the finished turn — a
      deliberate cut, not an omission: `st.write_stream` would have been a second streaming
      path for a frontend the sprint was moving away from.

- [ ] **Contracts at public boundaries are undocumented** — the workflow's rule already
      allows a docstring that states a contract the code can't express; apply it where
      fallback behaviour, security assumptions and error guarantees are invisible from
      the signature (`ToolResult` invariants, `CoreError.user_message`, validation
      ordering). Not a policy change — no docstrings elsewhere.
      → continuous, checked at each merge. Be ready to say what each public service
      accepts, returns and promises. **Stays unticked by design** — it is a standing habit
      with no last increment, so an empty box here reads as "still in force", not "not done".

## Reviewer's optional suggestions

Recorded with a decision, not scheduled — none is in the sprint-4 story cut.

- [ ] **RAG evaluation set** (10–20 questions with expected sources) — the most useful
      of the four, and it would give
      story 1's "decide whether to retrieve" a measurable answer. Candidate if the
      stretch story is dropped.
- [ ] **PostgreSQL + pgvector instead of Chroma** — deferred. It is an adapter swap
      behind the `Retriever` port, so it stays cheap to do later; nothing this sprint
      needs it.
- [ ] **Second-stage semantic reranking** (wider candidate set through a cross-encoder
      before context selection) — deferred; retrieval quality is not this sprint's axis.
- [ ] **Richer chunk metadata** (headings, sections, page numbers, doc type) — deferred,
      but it is what would make citations better than filenames. Revisit with the
      evaluation set.

## Found by the story-1 review

- [x] **Citation numbers restart each turn** — `[1]` names one document this turn and
      another the next, so a model that echoes an earlier `[1]` while paraphrasing its own
      previous answer has it resolved against *this* turn's sources
      (`core/services/agent.py`). Pre-dates the agent — sprint 3 numbered per turn too.
      → **Done in story 3**: the checkpointer makes the thread the owner of `sources`, so
      numbering runs the length of the conversation. A document keeps its number when it
      is found again, a new one takes the next, and an answer echoing an earlier `[1]`
      resolves to the source the user was shown.

## Carried over from the manual test run

- [x] **#5 Tool results shown raw and unlabelled** — `chat.py:106` renders bare payloads
      with no tool name, and internal recovered-from failures leak into the user's view.
      → covered by **story 2** (the trace names the step, the tool and its arguments).
      **Done in story 2**: `ChatResult.tool_results` is gone, so a payload has nowhere to
      print but the trace, which names the tool and its arguments. The second half —
      leaking failures — took the story-2 review to spot: a tool's own exception text was
      still shown verbatim, so `ToolRuntime` now passes on the kind of an exception that
      merely escaped, and quotes only the `ValueError` a tool raised to explain itself.
- [ ] **#8 No way to remove a document or clear the store** — the sidebar lists sources
      with no chunk count, no removal, no clear (`app/ui/chat.py:34-39`).
      → memory clearing lands in **story 3**; document removal stays open here.
- [x] **#10 Default DB path is CWD-relative** — `CORA_DB_PATH` exists, but the default
      `.cora/chroma` still means launching from another directory starts an empty store.
      → own small slice; fix or document loudly before the review.
      **Closed on the second branch**: `README.md:121-127` states it for every path cora
      persists to — Chroma, remembered facts and the text behind each citation are all
      documented as relative to the working directory. The behaviour is unchanged and
      deliberate; a reader who launches elsewhere is told why the store looks empty.

## Found by the single-cora-package review

- [x] **A blank `CORA_MEMORY_PATH` throws away everything the user asks to be
      remembered** — `config.py` reads the variable with `env.get(..., DEFAULT)`, so a
      variable blanked rather than deleted survives as `""`, and `sqlite3.connect("")`
      does not raise: SQLite opens a private temporary database that is deleted with the
      connection. The `remember` tool works, the panel lists the facts, and the next
      start has none of them — no error anywhere. Pre-dates the sprint; `CORA_MODEL`
      already reads a blank as unset, and every path variable should.
      → taken on `fix/submission-blockers`. `_model` is the shape to copy, and the fix is
      the whole class of variable rather than the one that was found: a blank string is
      not a value anywhere in `from_env`. Test list:
  - [x] a blank `CORA_MEMORY_PATH` reads as unset, so remembered facts survive a restart
  - [x] a blank `CORA_DB_PATH` reads as unset
  - [x] a blank `OPENROUTER_BASE_URL` reads as unset — same shape, same silent failure
  - [x] surrounding whitespace is stripped from a path that *is* named
  - [x] a named path still wins over the default — already covered by
        `test_from_env_reads_every_field`, so no new test
  - [x] a blank `OPENROUTER_API_KEY` stops startup by name rather than becoming a 401
        the user reads as "temporarily unavailable", and a pasted key keeps neither
        space — found by the branch review, which called the claim above overclaimed
  - [x] a blank count reads as unset rather than refusing to start the app

## Found by the `fix/submission-blockers` review

`ai-code-reviewer` on the accumulated branch diff, before the branch merged. It cleared
the two re-specified tests as honest and found four things inside the scope the branch
claimed to close — the pattern in three of them is the same: the fix was applied to the
case that was reported rather than to the class it belongs to.

- [x] **The medication branch still refused a mention** — `about_medication` fired on the
      word alone, so "I'm on blood pressure medication — what cardio is safe?" was
      refused: the reported bug, moved one keyword over, and the class docstring claimed
      behaviour the code did not have. A subject now has to meet a request.
- [x] **The rule missed whole families of request** — no treatment verb at all ("what
      should I do about my thyroid"), and no phrasing for "is that diabetes" or "could I
      be pregnant". Widened, with the two interrogative shapes as regexes so that the
      condition has to be *what is asked about* — checking the wider list by hand turned
      up two false positives of its own ("I have diabetes, am I training enough?"), and
      both are now pinned as allowed.
- [x] **`OPENROUTER_API_KEY` was the one setting the blank rule skipped**, so a blanked
      or space-padded key reached OpenRouter and came back a 401 the user reads as
      "temporarily unavailable". Counts too. Ticked into the blank-setting item above.
- [x] **A ticked box with no test that can fail** — story 12's small-talk criterion was
      asserted against a scripted model returning the answer it was scripted to return.
      The integration test now asserts what it can (the reminder's wording), and the
      claim that a *model* obeys it moved to the `llm` tier where it can fail.
- [x] **Context overflow and a rejected key both landed on "please try again"** — no
      retry fixes either, and the thread is persisted, so an overflow repeats until the
      user starts a new conversation. Both are categories now; `_CATEGORIES` became an
      ordered tuple because the provider's classes overlap by inheritance.
- [x] **The deadline was per request, and the output cap was the provider's** — 60s × 3
      attempts × 8 rounds is what a user waits behind a spinner with no cancel. The
      timeout is 20s and `max_tokens` is cora's own, so a truncated answer is a number
      we chose.
- [x] **The trace told neither silence apart**, rendering both as "no matching
      documents" in the panel the user opens to find out why. Story 15 took the gate that
      held the two silences; the one that survives is the search tool's own — a store
      nothing was uploaded to says exactly that.
- [x] **Assertions on a fake's constructor kwargs** — replaced with the real client's
      state, which is what catches a keyword this library stops reading; the subsumed
      wrapping test is gone and `httpx` is a declared dev dependency.
- [x] **`found == [] ⇒ nothing uploaded` rested on untested infrastructure** — an
      integration test now pins that a fresh Chroma collection answers with no hits.

## Found by the story-21 review

`/code-review` on the merged commit, after the story closed. Two of the five are the
story's own criterion not actually being met by the fix that claimed it; the rest are a
crash the current caller cannot reach, a banner with no end, and a comment left in the
present tense.

- [x] **The patch kept the nodes but not the selection** — `drawn.nodeValue = …` is DOM's
      replace-data across the whole node, and its steps pull every live-range boundary
      inside the node back to offset `0`. So a reader selecting a phrase in the paragraph
      still being written lost it on the very next piece — the criterion the story is
      named for. Only *settled* nodes, left alone because their text compares equal,
      survived. Text that merely grew is now appended to, which moves no boundary already
      in it. happy-dom adjusts ranges on neither path — the same blind spot story 21
      recorded for node removal — so the assertion moved to a browser: see the tier below.
- [x] **Anything that was neither element nor text crashed the page** — a comment node
      matches on `nodeType` and `nodeName`, fell through to the element branch and threw
      on `undefined.attributes`; from `useLayoutEffect` that unmounts the conversation
      tree, so a blank page mid-answer. Unreachable only because `answer.ts` builds
      markdown-it with `html: false`, a precondition `patch`'s own docstring does not
      make. The branch now asks whether a node *is* an element rather than whether it is
      text.
- [x] **The notice had no end** — `start()` cleared the entries, the read document and the
      load banner but not the notice, so "Added notes.md — 12 passages." stood over every
      later conversation until the reader happened to upload again. A new session is the
      reader clearing their desk.
- [x] **More than `on_text` left the categories** — adding a piece to the whole moved out
      with it, and the library refuses a field two pieces disagree about, so a provider
      streaming reasoning oddly raised a bare `TypeError` out of `complete()` instead of a
      category. Only the sink call needed to move.
- [x] **A comment claimed a marker the tests no longer carry** — story 21's outer tests
      read as still held under `test.fails`, in the present tense, above three plain
      `test` calls.

## Found by the second `fix/patch-selection` review

The same reviewer over the accumulated branch diff. Both findings are the fixes above not
having reached the whole of what they claimed.

- [x] **A failure nobody modelled was kept nowhere** — categorising the chunk merge closed
      the raw `TypeError` and, with it, the traceback: the routes deliver a `CoreError`'s
      sentence without logging it, and only the unmodelled `except Exception` logged. So
      the reader was told the model is temporarily unavailable and the operator had
      nothing to read. This was already true of every provider error matching no category,
      so the log went where that decision is made rather than at the merge.
- [x] **`reopen` left the notice standing** — `start` clears it, but reopening an earlier
      conversation from the rail left an upload's notice above a conversation that predates
      it. The two are the same boundary and now clear the same things.
- [x] **The append had nothing defending it** — the fix the branch is named for passed
      and failed identically under happy-dom, so reverting `appended` to a whole-node
      write left all 91 tests green. Rather than assert the call, the criterion moved to
      a browser: `make ui-test-browser` runs `browser/selection.test.ts` in Chromium,
      where selecting a phrase in the paragraph being written and losing it is exactly
      what the mutation now does. It stays off `npm test` and out of the pre-commit hook —
      a browser is not something a commit should wait for — and CI runs it as its own
      steps in the `ui-tier` job, so a revert cannot merge green.

## Found by the third `fix/patch-selection` review

One real race left by the notice fixes, three infrastructure findings on the browser tier,
and one finding that turned out not to be reachable.

- [x] **The notice could still land where it does not belong** — `upload` was the one async
      result in `App.tsx` with no race guard, while `loaded` compares `loads.current` and
      `ask` compares `here.current`. Ingestion takes seconds and neither the picker nor
      *New session* is disabled while it runs, so a reader who left mid-upload got the
      notice on a conversation the upload never happened in — and with nothing left to
      leave, `start()` early-returns and nothing could take it away. The notice is now
      stamped with the conversation the upload was started in; the refresh and the failure
      are not, because a document is added wherever the reader is.
- [x] ~~`reopen` clears the notice even when the reader has not gone anywhere~~ — not
      reachable: `SessionsPanel` disables the row for the current thread, so `reopen` only
      ever runs for another conversation. Caught by the test written for it, which passed
      against unfixed code.
- [x] **`README.md` called the browser tier "not a gate"** while CI runs it as a step of
      `ui-tier` — a red selection test blocks the merge, which is the point. It is not a
      *local* gate.
- [x] **`ui-test-browser` was missing from `.PHONY`**, alone among the targets: a file of
      that name in the repo root would silently make it a no-op.
- [x] **The browser's shared libraries came from the runner image** — `--with-deps` as well
      as `--only-shell`, so an `ubuntu-latest` rotation cannot fail every PR on a step that
      has nothing to do with the diff.
