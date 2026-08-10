# Sprint 4 — feedback backlog

The sprint-3 reviewer's findings, plus the open items from
`docs/sprints/3/manual-test-findings.md`, as tracked checklist items. Day-one
artefact per `docs/workflow.md`: feedback gets ticked here, not remembered.

Each item names where it was verified in today's code and how it lands — inside a
sprint-4 story from `docs/sprints/4/spec.md`, or as its own slice.

## Reviewer findings

- [ ] **Indirect prompt injection through document text** *(reviewer: biggest issue)* —
      retrieved chunks are concatenated into the system message
      (`core/services/chat_engine.py:107-110`), so an instruction hidden in an uploaded
      document carries the same authority as cora's own rules; the injection rule only
      sees the user's question (`core/services/validation.py`). Move retrieved text into
      a clearly marked user/tool message and label it untrusted data.
      → own slice, **before story 1** (the agent widens the blast radius: it will feed
      tool output back too).

- [ ] **No grounding or scope decision** — the prompt asks the model to ground its answer
      (`plugins/fitness/__init__.py:10`) but nothing enforces or tests it, so an
      out-of-domain question is answered from model knowledge. Add a tested rule that
      declines unsupported answers, evaluated against in-domain, out-of-domain and
      weak-retrieval cases. Also manual finding #6.
      → own slice, folded into **story 1** (grounding becomes one of the agent's steps).

- [ ] **Planner JSON is hand-parsed and fails silently** — `parse_plan` scrapes fences and
      braces, and a parse failure falls back to plain search with no signal
      (`core/services/query_planner.py:22-23,56-77`). Use structured output
      (`with_structured_output` / `response_format` with a JSON Schema) at the adapter
      boundary, and make the fallback observable.
      → own slice; do it while the retrieval path is being reshaped in **story 1**.

- [ ] **Model adapter swallows everything** — every provider exception becomes one generic
      `LlmError` (`adapters/openrouter_chat_model.py:73-77`), with no timeout, no retry
      policy, and `finish_reason`/usage discarded (`to_model_reply`), so a truncated or
      empty completion is treated as a successful answer. Set an explicit timeout and
      retry, preserve error categories, reject empty/truncated finals.
      → own slice, **before story 1** — the agent multiplies model calls per turn.

- [ ] **Medical filter is substring matching** — `MedicalSafetyRule`
      (`plugins/fitness/safety.py:20-25`) refuses any message containing `diabetes`,
      `pregnan`, `blood pressure`…, so "I have diabetes, how should I train?" is blocked
      outright. Distinguish diagnosis/medication requests from training questions that
      can get cautious guidance with a caveat. Also manual finding #7.
      → own slice, inside **story 6** (guard rails).

- [ ] **No streaming** — the port returns a finished reply and the UI blocks on a spinner
      (`core/ports/chat_model.py`, `app/ui/chat.py:93`). Stream through the model
      boundary and render with `st.write_stream`.
      → own slice, after **story 2** (the trace and the stream share the same surface).

- [ ] **Contracts at public boundaries are undocumented** — the workflow's rule already
      allows a docstring that states a contract the code can't express; apply it where
      fallback behaviour, security assumptions and error guarantees are invisible from
      the signature (planner fallback, `ToolResult` invariants, `CoreError.user_message`,
      validation ordering). Not a policy change — no docstrings elsewhere.
      → continuous, checked at each merge. Be ready to say what each public service
      accepts, returns and promises.

## Reviewer's optional suggestions

Recorded with a decision, not scheduled — none is in the sprint-4 story cut.

- [ ] **RAG evaluation set** (10–20 questions with expected sources, compared across
      plain / advanced / hybrid) — the most useful of the four, and it would give
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

## Carried over from the manual test run

- [ ] **#5 Tool results shown raw and unlabelled** — `chat.py:106` renders bare payloads
      with no tool name, and internal recovered-from failures leak into the user's view.
      → covered by **story 2** (the trace names the step, the tool and its arguments).
- [ ] **#8 No way to remove a document or clear the store** — the sidebar lists sources
      with no chunk count, no removal, no clear (`app/ui/chat.py:34-39`).
      → memory clearing lands in **story 3**; document removal stays open here.
- [ ] **#10 Default DB path is CWD-relative** — `CORA_DB_PATH` exists, but the default
      `.cora/chroma` still means launching from another directory starts an empty store.
      → own small slice; fix or document loudly before the review.
