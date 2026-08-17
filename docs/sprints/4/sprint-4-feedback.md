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
      **Done in story 8** (`story-08.md`), after it showed up in use: a plugin now carries a
      `grounding` reminder, and a first answer with no search behind it is sent back through
      the model once. Scoping stays with the model — the reminder tells it to answer small
      talk as it did — so a greeting still costs no retrieval.

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

- [ ] **No streaming** — the port returns a finished reply and the UI blocks on a spinner
      (`core/ports/chat_model.py`, `app/ui/chat.py:93`). Stream through the model
      boundary and render with `st.write_stream`.
      → own slice, after **story 2** (the trace and the stream share the same surface).

- [ ] **Contracts at public boundaries are undocumented** — the workflow's rule already
      allows a docstring that states a contract the code can't express; apply it where
      fallback behaviour, security assumptions and error guarantees are invisible from
      the signature (`ToolResult` invariants, `CoreError.user_message`, validation
      ordering). Not a policy change — no docstrings elsewhere.
      → continuous, checked at each merge. Be ready to say what each public service
      accepts, returns and promises.

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
- [ ] **#10 Default DB path is CWD-relative** — `CORA_DB_PATH` exists, but the default
      `.cora/chroma` still means launching from another directory starts an empty store.
      → own small slice; fix or document loudly before the review.

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
