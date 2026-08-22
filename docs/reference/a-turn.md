# A turn, step by step

The two calls a frontend makes, and what each one does in order. The shape they take is
drawn on [a turn](../happy-path.md#a-turn-as-a-frontend-asks-for-one), and the round inside
it on [the one after](../happy-path.md#a-round-as-the-graph-walks-it).

**`agent.answer(question, thread_id) -> ChatResult`** — `engine/agent.py`, returning `domain/chat_result.py`

The conversation belongs to the thread, not to the caller: a turn is seeded with the
question alone, and the graph's checkpointer supplies everything said before it. The
frontend names the thread: it opens on one and mints another when the reader starts a new
session, so the conversation on screen is the conversation cora is answering in.

1. **Prepare** — check the question against one ordered tuple of rules: cora's own first (not empty, at most 4000 characters), then every loaded plugin's, in the order they were named. If a rule says no, raise `InputRejectedError`; the model never sees the question. Screening for prompt injection is one of those plugin rules — `cora.plugins.security` — and not the engine's, so cora as installed screens nothing until a deployment names it. Then add the question to the thread's transcript and write this turn's **brief**: cora's preamble, cora's own rules (call `search_documents`, cite `[n]`, call `remember` when the user asks to be remembered, call `ask_user` when what is remembered holds one fact at two values and nothing says which is current), one section per plugin under its `name`, and whatever is already remembered about the user — labelled as notes rather than rules, and stated last, because a fact is kept user input. The brief is rewritten each turn, so a ten-turn thread carries one, and a fact learned mid-conversation is in hand the next turn. Rules see the question only.
2. **Model** — one round. The model is offered `search_documents`, `remember` and `ask_user` beside the plugin's tools. It is sent the brief, then the previous turns' words — the last `CORA_HISTORY_TURNS` of them (default 20; `0` means no history) — then this turn verbatim. Old tool calls and their results stay in the thread but out of the prompt. It either answers or asks for tools.
3. **Ask, if it asked** — a round that called `ask_user` stops here. The model states the question and the ways out of it in its own words; the run is parked in the checkpointer and the turn ends with no answer, raising `TurnPaused` rather than returning one. `agent.resume(chosen, thread_id)` picks it up on the label the reader chose — or on nothing, if they declined — and `agent.pending(thread_id)` is how a page that arrived after the pause finds the question. This runs *before* the round's tools, and that order is load-bearing: a resumed step is replayed from its first line, so a tool that had already run would run a second time on the way back.
4. **Tools** — run what it asked for, in order. A result that can cite itself — a set of search hits — is numbered `[n]` continuing from the numbers the *conversation* has already handed out, so `[1]` means one document for as long as the thread lives, and comes back as a `tool` message marked *untrusted document data*. Any other result is fed back exactly as it renders.
5. **Round again, or stop** — the router reads the model's last reply. A reply asking for tools goes back to step 2, at most `CORA_MAX_TOOL_ROUNDS` times (default 8), after which `ToolLoopLimitError` apologises. A reply that answers ends the run. Rounds are counted from where this turn began in the transcript, so the budget is the turn's and a long conversation cannot exhaust it.
6. **Return** — the answer, the passages it really cited (only the `[n]` numbers that appear in the reply, with duplicates removed, resolved against every source the conversation has registered), and this turn's trace — the thread arrives carrying every step of every earlier turn, and replaying those would show work this turn never did.

**`kb.add_file(data, filename) -> int`** — `engine/knowledge_base.py`

1. **Dedupe** — make a SHA-256 hash of the file. If the store already has this hash, stop and return `0`.
2. **Ingest** — the file must be `.txt`, `.md`, or `.pdf`, at most 10 MB, and not empty after cleaning. Each problem raises its own `IngestionError`.
3. **Chunk** — cut the text into pieces of 1000 characters that overlap by 150. Cut at the largest natural break that fits: paragraph, then line, then space, then single character.
4. **Embed and store** — turn each chunk into a vector (a list of numbers) and save it with its origin (source, index, offset, file hash). Return the number of chunks.
