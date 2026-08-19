# Manual test findings — the React shell

Exploratory run against the real stack, driven by hand in a browser: Vite on 5173
(`make ui`) proxying `/api` to `make run-env-react`, real OpenRouter model, real
embedder, real persistent Chroma, fitness plugin. Started 2026-08-19 on branch
`fix/react-ui-findings`.

Findings were reported one at a time as they were hit, and the run only collected
them — nothing was fixed while the sweep was open. It is closed; *Order of work* below is
the triage. Each item taken on gets a failing test that reproduces it, then the fix, and
then it leaves this file for the story that closed it. Items larger than a tweak become a
story.

The sweep found #1–#15; the branch review that closed it found #16–#22, checking the sprint
against `spec.md` found #23–#24, and re-checking three points carried from earlier reviews
found #25–#26.

**What is left here is what is still open.** The fixed ones — #2, #16–#23 and #26 — have
been removed: they were the triage's *Before submission* and *Real bugs, next* blocks, closed
by
`done/story-20.md` and `done/story-21.md`, which name them and carry the test lists they
became. Anything found while fixing them is in `sprint-4-feedback.md`.

**The numbers do not move.** Those two stories cite them, so the gaps are where the closed
findings were rather than a renumbering. Line references are re-anchored as the code
moves — last checked 2026-08-19 against `a2b568c`.

## Order of work

**Cheap, one chrome pass**

- **#11, #7, #9a, #3c** — four standing help paragraphs; remove them.
- **#6** — remove the "1 cited passage · highlighted" caption, after giving four tests a
  better handle.
- **#14** — rename the PLAN tab to STEPS.
- **#1** — give the cited passage a warm amber highlight instead of the page's blue.

**Layout, one decision first**

- **#15, #4** — rails start hidden and become draggable, once persistence is settled.

**Stories**

- **#12a** — add a `kind` to `Plugin` so the page offers only switchable ones.
- **#3** — make every indexed document openable, which needs the documents list to carry an
  upload.
- **#5** — make a highlighted passage link back to its citation.
- **#8** — let a conversation be deleted, across both stores that hold it.

**The prompt, verifiable only on the `llm` tier**

- **#25** — tag the brief's sections in XML so instruction and data differ by shape, not
  only by wording.

**Design before test list**

- **#13** — a settings section, scoped deliberately since #4, #10 and #12 all want one.
- **#10** — a translation seam, covering the API's prose as well as the page's.
- **#12b** — switching plugins on a live agent.
- **#9b** — per-session memory, which points against what memory currently is.

**After review**

- **#24** — tag the sprint-4 submission and write the retrospective.

## Findings — the sweep

1. **The cited passage is highlighted in the page's blue, not a warm callout colour.**
   *Improvement.* Open an answer's citation, and the cited chunk in the source pane is
   tinted `--accent-tint` with an `--accent` left rule — the same blue the page already
   uses for links, focus rings and the send button, so the highlight reads as "this is
   interactive" rather than "this is the quoted passage"
   (`frontends/react/ui/src/styles.css:638-644`). It should be a warm amber callout
   instead: amber tint, amber left rule, text left legible. There is no warm token in the
   palette yet — the only non-blue accent is `--magenta`, which is spoken for by
   destructive actions (`styles.css:1-37`), so this adds one.

3. **Every indexed document should open, cited or not — and then the rail needs no
   paragraph to explain itself.** *Improvement.* Three things, one rail
   (`frontends/react/ui/src/components/DocumentRail.tsx`):
   - **Uncited documents are unclickable.** A row is `disabled={!cited.has(name)}`
     (`DocumentRail.tsx:40`), so a document that this conversation has not cited cannot be
     read at all. Opening it should work like any other.
   - **An uncited document opens with nothing marked.** This part comes free: `passagesIn`
     filters the answer's citations by document, so an uncited one yields `[]` and
     `DocumentBody` draws plain paragraphs (`App.tsx:159`, `DocumentBody.tsx:53-58`).
   - **The paragraph of help text goes** (`UNCITED`, `DocumentRail.tsx:8-9`), with nothing
     in its place — and once every document opens, the sentence it carries is no longer
     true anyway.

   The work is not in the rail, it is in *which upload to read*: text is served per upload
   hash (`GET /api/uploads/{upload}`, `api.py:68,324`) and the page only ever learns a
   hash from a citation (`uploadOf`, `App.tsx:141-148`), while `/api/documents` returns bare
   filenames (`knowledge_base.list_sources`). So an uncited document has no upload to open
   until the documents list carries one — an API change, which makes this story-sized
   rather than a tweak. It also decides what "the document" means when one filename covers
   two uploads: presumably the newest.

4. **The two rails are a fixed width; they should be draggable.** *Improvement.* Both
   rails are flex items with a hard basis and floor — `flex: 0 1 232px; min-width: 180px`
   for the documents rail and `flex: 0 1 360px; min-width: 268px` for the panels rail
   (`frontends/react/ui/src/styles.css:161-163,513-515`) — so a long filename truncates and
   a citation pane cannot be widened to read a passage. Wanted: a drag handle on each inner
   edge, within a min/max, with the conversation column absorbing the difference
   (`.columns`, `styles.css:111-118`).

   Open decisions this carries: whether a chosen width survives a reload — the page persists
   nothing client-side today, `localStorage` appears nowhere in `ui/src` — and whether the
   handle is keyboard-operable, which the vitest tier can assert and a mouse-drag cannot.

5. **A highlighted passage should link back to the citation in the answer.** *Improvement.*
   Today the link runs one way: `[1]` in the answer is a
   `<button class="cite" data-cite="1">` that opens the source pane and scrolls to the
   passage (`frontends/react/ui/src/answer.ts:58`, `Answer.tsx:159,171`). Going back is
   manual. Clicking a mark should scroll the conversation to the `[n]` it belongs to, and
   where a mark answers to more than one, offer the choice.

   The blocker is in `DocumentBody`: `merged()` unions overlapping spans into a single
   `<mark>` and keeps only its start and end, so the mark no longer knows which citations
   produced it (`DocumentBody.tsx:51-58,75`) — and it is a bare `<mark>`, not a button,
   so it has neither click target nor keyboard reach. Both are the same change: merge
   spans *with* the citation numbers that fed them, and the multi-citation case the
   improvement asks about is precisely a merged mark, plus the same passage cited twice in
   one answer. The scroll target already exists — `[data-cite="n"]` — and only the newest
   answer is ever marked (`App.tsx:154-165`), so the jump stays inside one answer.

6. **The "1 cited passage · highlighted" caption in the source rail is noise.** *Bug —
   remove.* The caption sits under the filename in the source panel
   (`frontends/react/ui/src/components/SourcePanel.tsx:22,29-32`) and says what the reader
   can already see: the passages are marked on screen. Its other branch, `not cited in this
   answer`, is the one that carries information — worth deciding whether that survives when
   #3 makes every document openable, since the uncited case is about to become ordinary
   rather than exceptional.

   Six assertions across four tests in the vitest tier read this exact string
   (`App.test.tsx:219,588,600,620,641`, `SourcePanel.test.tsx:54`), several of them using it
   as the proxy for "the source pane opened on this document" — so removing the line means
   giving those four a better handle, not just deleting the text.

7. **The plan panel's explanatory footer should go.** *Improvement.* "cora
   chose these steps. Nothing here is a fixed pipeline — the tools come from the loaded
   plugin." is a paragraph under the steps
   (`frontends/react/ui/src/components/PlanPanel.tsx:5-6`, `FOOTER`). It explains the panel
   once and then costs vertical space on every answer.

   Same shape as #3's help paragraph, and the panels have two more of these — the memory
   panel's `INTRO` (`MemoryPanel.tsx:4`) and each panel's empty-state `NOTHING`
   (`SourcePanel.tsx:4`, `SessionsPanel.tsx:3`, `PlanPanel.tsx:4`). Empty states earn
   their words; standing explanations of a panel that is already full do not. Worth doing
   as one pass over the rail rather than three separate deletions.

8. **A conversation can be opened but never deleted.** *Improvement.* The sessions panel
   lists every past conversation as an open-button and nothing else
   (`frontends/react/ui/src/components/SessionsPanel.tsx:15-25`), so a thread started by a
   mistyped question is there for good.

   This one goes all the way down, and the depth is the point:
   - The `Conversations` port has `record`, `turns`, `sessions` and no way to remove one
     (`src/cora/ports/conversations.py:15-19`), so the SQLite adapter grows a method too
     (`src/cora/adapters/sqlite_conversations.py:32-77`).
   - **Two stores hold a thread.** The turn log is cora's; the agent's own memory of the
     thread belongs to the runner's checkpointer, keyed by the same `thread_id`
     (`src/cora/adapters/langgraph_runner.py:68-79`, port docstring at
     `conversations.py:7-9`). Deleting only the log leaves a thread that is invisible but
     still remembered — reopen that id and the agent picks up where it left off. Deletion
     has to name both, or say deliberately that it doesn't.
   - Memory is the precedent to copy, not invent against: it already ships per-item and
     clear-everything deletes end to end (`DELETE /api/memory/{key}` and `/api/memory`,
     `frontends/react/src/cora/frontends/react/api.py:71-72`; `MemoryPanel` draws both,
     with the destructive styling already in the palette).
   - Deleting the conversation you are *in* is its own case — the page has `start` for
     leaving a thread already, so delete-then-start is the likely shape.

9. **The memory panel's standing intro should go too — and memory per session is an open
   question.** *Improvement, two parts.*
   - The removal half is #7's pass over the rail: `INTRO` — "What cora carries between
     sessions. Remove a line and it stops assuming it." — is drawn above the facts whenever
     there are any (`frontends/react/ui/src/components/MemoryPanel.tsx:4,15`). Its
     empty-state sibling stays.
   - **Per-session memory is a design question, not a tweak, and it points the other way
     from what memory currently *is*.** The `Memory` port is deliberately one user's facts
     across all sessions — "What the agent keeps about one user between sessions", with
     which user and where the facts live left to the adapter
     (`src/cora/ports/memory.py:11-25`). Scoping facts to a thread is a different feature,
     not a setting on this one: it would need remembering to know which thread it is in
     (`remember(text)` takes none), and a fact learned in one conversation would stop
     applying in the next — which is the behaviour the panel's own sentence promises.
     Recorded as raised, not as decided; if it is wanted, it wants its own story and
     probably a sharper statement of the problem it solves.

10. **The UI's text is hardcoded English; translating it needs a way in.** *Improvement —
    needs design before it needs a test list.* Every visible string is a module constant
    next to the markup that draws it (`NOTHING`, `INTRO`, `UNCITED`, `FOOTER`, `UNKEPT`, …
    — about twenty across `frontends/react/ui/src`), so there is no seam to swap.

    The scope is wider than the React page, which is what makes this a design question:
    - **Server-side user text.** The API answers with English sentences of its own —
      `NO_FILE`, `OVER_CEILING`, `UNKEPT`, `NO_LENGTH`
      (`frontends/react/src/cora/frontends/react/api.py:170-176,333`) — plus every
      `user_message` on a raised error. Those are drawn verbatim by the page, so a
      translated UI over an English API is half-translated. Either the server sends a code
      the page renders, or the page never gets prose from the server.
    - **The Streamlit frontend** has its own copy of the same problem
      (`frontends/streamlit/.../formatting.py`), so whatever seam is chosen wants to sit
      where both can reach it — or be chosen knowing only one frontend gets it.
    - **The model's answer** is not UI text at all: language there comes from the plugin
      prompt and the user's own question, and is a separate decision from labels.
    - **The test tiers assert on literal English** — the vitest suite matches strings like
      "1 cited passage · highlighted" (see #6), and the Python tiers match `user_message`
      text. Whatever seam lands, those assertions have to go through it too, or the suite
      pins English in place by force.

11. **The plugin menu's footnote about `CORA_PLUGINS` should go.** *Bug — remove.* "Named by
    the deployment in CORA_PLUGINS, and bound when cora was assembled." is the foot of the
    plugin popover (`frontends/react/ui/src/components/Header.tsx:17,81`, `FIXED`). It
    explains cora's deployment model to a reader who cannot act on it — the badge already
    says which plugin is loaded, and the menu already shows each module's dotted path.

    Cheapest of the removals so far: no test in the vitest tier matches this string, so it
    is a deletion of the constant and its `div`. The popover's remaining text — the heading
    and "No plugin is loaded." — is not in scope unless #7's rail pass reaches the header
    too.

12. **Plugins should be classified by kind, so the page offers only the switchable ones.**
    *Improvement — design first.* A `Plugin` is a name plus whatever it contributes:
    instructions, tools, validation rules (`src/cora/ports/plugin.py:51-65`). Nothing says
    what *sort* of plugin it is, so every loaded module is one undifferentiated list — the
    header shows all of them together (`/api/plugins`,
    `frontends/react/src/cora/frontends/react/api.py:74`; `Header.tsx:63,74-80`) and the
    engine merges all their tools and instructions into one brief (`assembly.py:72-76`).

    Two separable pieces, and the first is cheap:
    - **A kind on the plugin.** The port's own docstring says a further kind of
      contribution should arrive as "a field with a default, not a break" — so a `kind`
      field, with the header filtering on it, needs no rework of the registry. The feedback
      backlog already wants a *security* plugin carrying stronger injection rules
      (`sprint-4-feedback.md`), and that is exactly a plugin a user must **not** be able to
      switch off from the page — so the classification has a second caller waiting.
    - **Switching, which does not exist at all.** Plugins are named in `CORA_PLUGINS` and
      bound once when cora is assembled (`config.py:126-128`, `assembly.py:143`);
      `/api/plugins` is `GET` only, and the badge is a read-only display. Letting the page
      change the loaded set means rebinding tools and instructions on a live agent, and
      deciding what that does to a conversation already in flight under the old set. That
      is a story of its own, not a filter on a menu.

13. **There is no settings section.** *Improvement — needs its scope named before it can be
    planned.* Nothing in the page is adjustable: every knob cora has is an environment
    variable read once when the process starts (`CORA_MODEL`, `CORA_TOP_K`,
    `CORA_HISTORY_TURNS`, `CORA_REASONING_EFFORT`, `CORA_MAX_TOOL_ROUNDS`,
    `CORA_MAX_OUTPUT_TOKENS`, `CORA_REQUEST_TIMEOUT`, the four store paths, `CORA_DEBUG`,
    `CORA_PLUGINS` — `src/cora/app/config.py`), and the API exposes none of them.

    It is a home several other findings are asking for — rail widths (#4), UI language (#10),
    the switchable plugin set (#12) — which is why it should be cut deliberately rather than
    grown by accretion. The line that decides the size:
    - **Page preferences** (widths, language, theme) belong to the browser, persist client-side
      and touch no Python. Cheap, and #4 needs the decision anyway.
    - **Engine settings** (model, `top_k`, history turns, effort) are read at assembly into
      objects that are then fixed, so exposing them means either rebuilding the app or
      threading a per-request override — the same problem as #12's switching, and the same
      question about a conversation in flight.
    - **Store paths and `CORA_DEBUG`** are deployment, not user preference, and should stay
      out however the rest lands.

14. **The "PLAN" tab is misnamed — it shows what cora did, not what it intends.** *Improvement.*
    The panel lists finished steps with a ✓ or ✕ each and an expandable result
    (`frontends/react/ui/src/components/PlanPanel.tsx:15-30`), and it is filled *after* the
    answer arrives. A plan is what is about to happen; this is the record of what happened.
    Every layer below already says so: the domain type is `TraceStep`
    (`src/cora/domain/trace.py:9`), and the panel's own empty state reads "The steps cora
    takes will appear here."

    **STEPS** is the label to take — it matches that empty state, claims exactly what is
    shown, and stays true when a step fails. `TRACE` is the alternative and matches the code
    exactly, but reads as a developer's word on a user's page.

    `TABS` doubles as the tab label and the state key (`App.tsx:13,43,223,398`), so the
    rename touches the union type, two `setTab` calls and six `role="tab"` lookups in the
    vitest tier (`App.test.tsx:179,183,189,511,833,958`) — mechanical, but not a one-line
    change. Worth splitting label from key if a second tab is ever renamed.

15. **Both rails should start hidden.** *Improvement.* They open on load —
    `useState(true)` for each (`frontends/react/ui/src/App.tsx:77,88`) — so a first-time
    reader meets three columns before they have asked anything, and the conversation, which
    is the point of the page, gets the middle third. Empty rails at that moment say little:
    no documents cited yet, no steps taken, no sessions.

    Flipping the two defaults is a one-word change each, but it collides with the vitest
    tier, which asserts on rail contents without opening anything, and with two findings
    already logged: whether the choice persists across reloads is the same question #4 asks
    about widths, and if it persists it is a preference and belongs in #13's settings. Also
    worth deciding whether a rail *opens itself* when it gains something to say — clicking
    a citation already forces the source tab (`App.tsx:168`), and that call is
    meaningless while the rail is shut.
