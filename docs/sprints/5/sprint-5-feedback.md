# Sprint 5 — feedback backlog

Day-one artefact per `docs/workflow.md`: every finding from the sprint-4 review becomes a
tracked checklist item here, so feedback is ticked rather than remembered.

Three sources feed it:

- **the reviewer**, verbatim in `docs/sprints/4/review-feedback.md`
- **the sprint-4 retrospective**, which stays on the branch `retro/submission-retrospective`
  and is not copied here — its actions are restated below in full, so this file stands alone
- **sprint 4's own open items**, carried from `docs/sprints/4/sprint-4-feedback.md` and
  `docs/sprints/4/manual-test-findings.md`

Each item says where it was seen and how it lands. The story it lands in is named against
the cut in `spec.md`; an item with no story is deferred there, with its reason.

---

## Reviewer findings

- [ ] **`README.md` does not convey the main idea** — *the reviewer's first point.* The
      opening is one or two sentences; a reader does not learn what the solution is for.
      The retrospective names the cause: the README was cut last, deliberately, and
      proposals for it were discarded. → the retro's own action is **write the paragraph on
      day one, before the code**.
      → **story 1**, and it is written first.

- [ ] **The two-store architecture is heavy for what it buys** — Chroma plus a SQL store
      duplicate the raw text, and the duplication exists to highlight a chunk inside its
      plain text. The reviewer's alternative, discussed in the review: one Markdown file per
      source document, addressed individually by the algorithm. Same capability, one store
      and a directory. A scratch note from the same week reached this independently.
      → **story 8**. It is an adapter swap behind the `Documents` port, which already
      exists; `sqlite_conversations.py` and `sqlite_store_memory.py` are untouched.

- [ ] **Multi-domain layout is unexplained** — with one domain the two stores work, but
      nothing says how they are laid out for a *second* domain: per-domain stores, shared
      store with a namespace, or something else. The reviewer asks for this in `README.md`,
      not only in the design. cora's whole pitch is that the domain comes from a plugin, so
      this is the pitch's missing half.
      → **stories 6 and 8**, in the code and in `README.md`. A scope owns its documents, so
      the layout is a directory per scope rather than a scheme to explain.

- [ ] **One agent should be a sequence of steps** — a single agent receives and processes
      the whole query; breaking the logical processes into an agentic workflow would be less
      fragile, more stable and easier to control. The retrospective records the same doubt
      held all sprint without acting on it, and the retro's action list makes it **the first
      story of the sprint**.
      → **stories 3 and 6**. The turn becomes *screen → route → focus → work → answer*,
      and the routing step is what makes a scope mean something. It lands third in the
      merge order: the README is day one and story 2 unifies the frontend, so nothing
      new is built for two screens.

## Retrospective actions

Restated from the sprint-4 retrospective (branch `retro/submission-retrospective`).

- [ ] **One gate, not four** — explain-back moves from every green step to every merge to
      main. Sprint 4 had four optional gates and skipped them; one checkpoint that gets held
      beats four that don't. If I can't say what a merge does and why, it doesn't merge.
      → in force from this sprint's first merge; no story, it is how a merge happens.
- [ ] **Read in the reader** — plans and branch diffs go through `md-read` before approval.
      The editing environment was doing double duty as a reading environment, and the reading
      half was the half that failed.
      → in force from story 1.
- [ ] **Refactor the tests, 20/80** — find the fifth of the 1,247 tests that carries most of
      the protection and extend only those; archive the rest under `tests` and delete the
      archive after the capstone. Membership is decided by what would go undetected, not by
      count.
      → a **chore** in `spec.md`, not a story: no failing test names it.
- [ ] **Break the one agent into a workflow** — first story of the sprint. Same item as the
      reviewer's fourth finding above; two routes reached it independently.
      → **stories 3 and 6**, third in the merge order — the reviewer's finding above says
      why the README and the one-frontend story go ahead of it.
- [ ] **README before the code** — the paragraph that conveys the idea gets written day one.
      → **story 1**.
- [ ] **An architecture note for the frontend before its first story** — sprint 4 had none
      and said so.
      → a **chore**, due before story 6 puts the scope pin on the screen.
- [ ] **Reviewer feedback as a backlog on day one** — this file. The only action from the
      previous retro that visibly changed behaviour.
      → this file, written before the story cut.
- [ ] **Decide about mid-sprint feedback rather than carrying it** — book it or strike it. An
      item knowingly ignored teaches that the list is optional.
      → open. Decide it at the first merge, not at the end.
- [x] **Use SDD for the capstone** — done, against the planning difficulty the retro names:
      OpenSpec drives planning from `openspec/`, `docs/workflow.md` says how it fits, and
      `openspec/config.yaml` carries this project's rules so the tool reads them instead of
      being reminded of them.

## Carried from sprint 4

Open when sprint 4 closed, still open now.

- [ ] **Stronger injection rules, and a scan of document content at ingest** — the rule is
      still two regexes
      (`plugins/security/src/cora/plugins/security/injection.py:6-15`), and nothing scans a
      document's text when it is added. Plugin composition is no longer the blocker: sprint 4
      made `CORA_PLUGINS` an ordered list and the guard ships as its own distribution. This is
      defence in depth behind the message-role fix, not a substitute for it.
      → **not this sprint** (`spec.md`, *Not in this sprint*). Story 9 says what the screen
      does not catch instead of implying it catches everything.
- [ ] **Contracts at public boundaries** — a standing habit, not an increment: be ready to say
      what each public service accepts, returns and promises. **Unticked by design**; an empty
      box reads as "still in force".
      → standing; every story carries it.
- [ ] **No way to remove a document or clear the store** *(finding #8)* — the sidebar lists
      sources with no chunk count, no removal and no clear. Memory clearing shipped; document
      removal did not.
      → **not this sprint** (`spec.md`, *Not in this sprint*), carried again. Cheap once
      story 8 makes a source a file, so it is the first thing added if the sprint runs early.
- [ ] **The page's heading outline and its tablist** — `SourcePanel`'s `<h2>` is the React
      page's only heading, and the `role="tab"` buttons have no `aria-controls` and no
      `role="tabpanel"` to point at. Referred back deliberately in sprint 4: the fix decides
      the whole outline and the tab/panel wiring together, so it is one accessibility story
      with its own criterion.
      → **not this sprint** (`spec.md`, *Not in this sprint*). Deferred, not dropped.

### Deferred suggestions, recorded not scheduled

- [ ] **RAG evaluation set** (10–20 questions with expected sources) — the most useful of the
      four, and the capstone is marked on evaluation: "how did you measure success" is one of
      the six presentation points.
      → **not this sprint**. Story 4 measures the *router* instead — retrieval is unchanged
      this sprint, so a number for it would be measuring sprint 4.
- [ ] **PostgreSQL + pgvector instead of Chroma** — an adapter swap behind the `Retriever`
      port. Cheap to do later; note that the reviewer's store finding above may decide it.
      → **not this sprint**. Story 6 empties the index of text — embeddings and offsets
      stay — but the engine behind the `Retriever` port is unchanged.
- [ ] **Second-stage semantic reranking** — a wider candidate set through a cross-encoder
      before context selection.
      → **not this sprint**; retrieval quality is not this sprint's axis.
- [ ] **Richer chunk metadata** (headings, sections, page numbers, doc type) — what would make
      citations better than filenames. Revisit with the evaluation set.
      → **not this sprint**; same reason.

## Found while re-cutting the sprint

The review said in conversation that cora is not a real agentic application — it is more like
agentic RAG. It is not in the write-up above, and it is what the sprint now answers.

- [ ] **cora can decide but cannot act** — every tool it owns reads its own documents, so a
      well-planned turn only ever produced a better answer. Reach, consequence and a gate in
      front of both.
      → **stories 7 and 8**, and it is the capstone's headline.
