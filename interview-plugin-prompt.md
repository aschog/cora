Build an **interview-preparation plugin** for cora, in this repo. This is a
plugin-authoring exercise, not a sprint story: skip OpenSpec and docs/workflow.md,
build `plugins/interview` as a workspace package shaped like `plugins/fitness`,
with tests. Read `docs/how-to/write-a-plugin.md` first and follow it exactly;
`plugins/fitness` and `plugins/travel` are the worked examples.

The underlying assignment is "build an interview prep app: frontend + OpenRouter +
system prompts + a security guard". cora already IS the app — chat page, OpenRouter
turn loop, document RAG, memory, citations, a prompt-injection screen
(`cora.plugins.security`), and an approval gate on effects. Do not rebuild any of
that: no frontend, no HTTP client to OpenRouter, no chat loop. The plugin
contributes only its domain, via the `Host` contract (`CONTRACT = 1`).

Scope everything under `scope="interview"`.

1. **Persona** — `register_instructions`: an interview-prep coach. First line says
   what the field answers (the router reads it). It should coach for questions,
   run mock interviews, and analyse job descriptions the user uploaded into the
   `interview` field's documents (that is cora's RAG — no code needed, just tell
   the model in the instructions to search them).

2. **Five system prompts, different techniques** — write five candidate
   instruction sets: zero-shot, few-shot (worked Q&A examples), chain-of-thought,
   role/persona, and structured-rubric. `CORA_PLUGIN_INTERVIEW_STYLE` (read via
   `cora.settings`) selects which one registers; an unknown value raises
   `PluginLoadError`. Try each against the same three questions, pick the best as
   the default, and record the comparison in `plugins/interview/PROMPTS.md`.

3. **Security guard** — a `SCREENING` handler refusing (a) attempts to extract or
   override the plugin's instructions and (b) requests to answer live in a real
   interview on the user's behalf. Return the refusal sentence; `None` otherwise.
   Register it under the `interview` scope — the system-wide injection screen is
   already the security plugin's job.

4. **Tools**
   - `start_mock_interview(role, seniority, difficulty, interviewer)` —
     difficulty `enum: easy|medium|hard`, interviewer `enum: strict|neutral|friendly`,
     all required. Declare `asks` building a card from the schema via
     `fields_of`/`missing_from` (submit action `needs_valid=True`, plus a "Not now"
     way out). `run` keeps the interview setup and a question counter in
     `cora.state` and returns the first question.
   - `evaluate_answer(answer)` — LLM-as-judge via `cora.delegate`: score the
     answer against the interview in `cora.state` on a rubric (correctness,
     structure, communication), keep a running score in state, return the verdict
     plus the next question. `cora.show` one line per evaluation.
   - `save_interview_report(filename)` — writes transcript + scores through
     `cora.output.write`, declared `effect=True`, registered only when
     `cora.output is not None`.

5. **Tests** — mirror `plugins/fitness/tests`: registration (a fake Host), the
   guard's refusals and passes, card-building for missing arguments, state
   round-trip across two tool calls. No live model calls: fake `delegate`.

Gates must pass: `uv run pytest`, `uv run ruff format . && uv run ruff check . &&
uv run ty check`. Then show me how to run it:
`CORA_MODEL=openai/gpt-5-mini`, `CORA_PLUGINS=cora.plugins.security,cora.plugins.interview`,
`CORA_SCOPES=interview`, and confirm `make plugins` lists the persona, the three
tools (`save_interview_report` marked as an effect), and the guard.
