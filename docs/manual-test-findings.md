# Manual test findings

Exploratory run against the real stack (real OpenRouter `openai/gpt-4o-mini`,
real sentence-transformers embedder, real persistent Chroma, fitness plugin) on
2026-07-27, branch `chore/manual-test-setup`.

Driven headlessly through `streamlit.testing.v1.AppTest` over
`src/cora/app/ui/streamlit_app.py` — same script, same widgets, same
composition root as `streamlit run`; browser automation was unavailable. The
server itself was also started with `streamlit run` and answered
`/_stcore/health` with `ok`. Scenarios: cold start on an empty DB, upload of
all three `samples/` files, warm start on a populated DB, RAG questions,
tool-calling questions, safety rejections, over-long input, malformed uploads,
and plain reruns after an error.

> **Status.** Findings 2, 3 and 9 are fixed on `fix/ui-error-handling` (PR #5)
> and verified against the real stack. The other seven are open — #1 is the
> highest-severity one remaining. The findings below are left as they were
> written, so this file stays a record of the run rather than a tracker.

## What works

- Cold start ~12 s (spinner shown), warm start ~3 s. Seed docs ingested, then
  `.txt` / `.md` / `.pdf` uploads all land and appear in the sidebar.
- Content-hash dedup holds: re-running with the same file attached, and
  restarting against a populated DB, add nothing.
- Retrieval is on target — the deadlift question retrieves
  `deadlift-form-guide.pdf` first, the protein question `protein.md` first.
- Tools are actually used for arithmetic: BMI 24.69 for 80 kg / 1.80 m,
  TDEE 2759 kcal and macros 144/76.6/373.3 g for the 30 y male profile. A
  tool call that failed schema validation was returned to the model as data,
  and the model recovered and re-called it correctly — no crash.
- Malformed uploads all produce typed, readable errors and no stack traces:
  empty `.txt`, whitespace-only `.md`, non-PDF bytes named `.pdf`, invalid
  UTF-8 `.txt`.
- Validation rules fire: over-long input and the medical-safety keywords are
  rejected with their user-facing messages.

## Findings

### 1. No conversation memory — every turn starts from scratch (high)

`ChatEngine.answer` builds `[system, user]` fresh per call
(`core/services/chat_engine.py:75`); prior turns are never passed to the model.
The thread in `st.session_state.messages` is display-only.

Observed: "I weigh 80 kg. Remember that." → "Got it! You weigh 80 kg."; next
turn "What did I just tell you my weight was?" → "I don't have access to any
previous information about your weight." The very first test question also
ended in "could you please provide your weight in kilograms?" — a question the
app is structurally unable to hear the answer to.

### 2. Rejected messages leave an orphaned bubble; the error disappears (high)

`_answer` appends and renders the user message *before* calling the engine
(`app/ui/chat.py:52-59`), so a `CoreError` leaves the user turn in
`session_state.messages` with no reply. The `st.error` is not stored, so the
next rerun drops the explanation and keeps the dangling question.

Observed: after "Should I take insulin before training?" was rejected, a plain
rerun showed the user bubble with no answer and no error anywhere. Same for the
over-long message and for whitespace-only input, which renders as an
**empty** user bubble.

### 3. Upload errors are sticky and unclearable (medium)

The mirror of #2. `st.file_uploader` keeps its value across reruns, so
`_documents` re-ingests and re-raises on every rerun
(`app/ui/chat.py:32-42`). A bad upload pins its error to the sidebar until a
different file is chosen — the `latin.txt` error was still displayed several
reruns later, during unrelated chat turns.

Also wasteful on the happy path: each rerun re-hashes the attached file and
issues a Chroma `contains` query.

### 4. The Sources panel lists retrieved chunks, not cited ones (medium)

`ChatEngine.answer` returns every source in the top-k
(`chat_engine.py:34,72`), regardless of whether the answer used it. README
promises "answers cite their sources".

Observed: "What is the capital of France?" → "The capital of France is Paris."
with four fitness documents listed as Sources. Every answer lists 3-4 sources
whether or not the text cites them.

### 5. Tool results are shown raw and unlabelled (medium)

`format_tool_result` (`app/ui/formatting.py:11`) emits the bare payload with no
tool name and no rounding, and passes internal validation failures straight to
the user.

Observed in one "Tool results" expander:
`24.691358024691358` (which tool? what unit?), and for the macros question the
three lines `{"bmr": 1780.0, "tdee": 2759.0}`,
`invalid arguments: 0 is less than the minimum of 1200`,
`{"protein_g": 144.0, "fat_g": 76.63888888888889, "carbs_g": 373.3125}` — the
middle line is a recovered-from internal retry that a user should not see.

### 6. No grounding or scope guard (medium)

Out-of-domain questions are answered from model knowledge with unrelated
sources attached (see #4). Nothing detects "the retrieved context does not
support this" or redirects off-topic asks.

### 7. Safety rule blocks legitimate training questions (low-medium)

`MedicalSafetyRule` (`plugins/fitness/safety.py`) matches substrings before
retrieval, so "I have diabetes — how should I train?" is refused outright
rather than answered with a see-your-doctor caveat. `pregnan` and
`blood pressure` behave the same way. Deliberate, but worth a decision:
mentioning a condition is not the same as asking for medical advice.

### 8. Document list is thin (low-medium)

Seed docs (`protein.md`, `energy_balance.md`) are indistinguishable from user
uploads in the sidebar, so a first-time user sees two unexplained documents.
There is no chunk count, no per-document removal, and no way to clear the
knowledge base — and the DB persists across restarts, so it only grows.

### 9. Successful uploads give no confirmation (low)

`knowledge_base.add_file` returns a chunk count that the UI discards
(`app/ui/chat.py:38`). Success is only inferable from the sources list
changing; a dedup no-op is indistinguishable from a fresh ingest.

### 10. Chroma path is hardcoded and CWD-relative (low)

`streamlit_app.py` calls `build(Config.from_env())`, so `db_path` stays at
`.cora/chroma` (`app/assembly.py:19,58-62`) — the only knob `Config` does not
expose. Launching from another directory silently starts a new, empty DB.
