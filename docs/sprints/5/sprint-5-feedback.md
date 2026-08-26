# Sprint 5 — feedback backlog

Day-one artefact per `docs/workflow.md`: every finding from the sprint-4 review becomes a
tracked checklist item here, so feedback is ticked rather than remembered.

Three sources feed it:

- **the reviewer**, verbatim in `docs/sprints/4/review-feedback.md`
- **the sprint-4 retrospective**, which stays on the branch `retro/submission-retrospective`
  and is not copied here — its actions are restated below in full, so this file stands alone
- **sprint 4's own open items**, carried from `docs/sprints/4/sprint-4-feedback.md` and
  `docs/sprints/4/manual-test-findings.md`

Each item says where it was seen and how it lands. **Where it lands is still open**: the
capstone story cut (`docs/sprints/5/spec.md`) is not written yet, so an item names the
change it becomes only once that cut exists.

---

## Reviewer findings

- [ ] **`README.md` does not convey the main idea** — *the reviewer's first point.* The
      opening is one or two sentences; a reader does not learn what the solution is for.
      The retrospective names the cause: the README was cut last, deliberately, and
      proposals for it were discarded. → the retro's own action is **write the paragraph on
      day one, before the code**.

- [ ] **The two-store architecture is heavy for what it buys** — Chroma plus a SQL store
      duplicate the raw text, and the duplication exists to highlight a chunk inside its
      plain text. The reviewer's alternative, discussed in the review: one Markdown file per
      source document, addressed individually by the algorithm. Same capability, one store
      and a directory. A scratch note from the same week reached this independently.

- [ ] **Multi-domain layout is unexplained** — with one domain the two stores work, but
      nothing says how they are laid out for a *second* domain: per-domain stores, shared
      store with a namespace, or something else. The reviewer asks for this in `README.md`,
      not only in the design. cora's whole pitch is that the domain comes from a plugin, so
      this is the pitch's missing half.

- [ ] **One agent should be a sequence of steps** — a single agent receives and processes
      the whole query; breaking the logical processes into an agentic workflow would be less
      fragile, more stable and easier to control. The retrospective records the same doubt
      held all sprint without acting on it, and the retro's action list makes it **the first
      story of the sprint**.

## Retrospective actions

Restated from the sprint-4 retrospective (branch `retro/submission-retrospective`).

- [ ] **One gate, not four** — explain-back moves from every green step to every merge to
      main. Sprint 4 had four optional gates and skipped them; one checkpoint that gets held
      beats four that don't. If I can't say what a merge does and why, it doesn't merge.
- [ ] **Read in the reader** — plans and branch diffs go through `md-read` before approval.
      The editing environment was doing double duty as a reading environment, and the reading
      half was the half that failed.
- [ ] **Refactor the tests, 20/80** — find the fifth of the 1,247 tests that carries most of
      the protection and extend only those; archive the rest under `tests` and delete the
      archive after the capstone. Membership is decided by what would go undetected, not by
      count.
- [ ] **Break the one agent into a workflow** — first story of the sprint. Same item as the
      reviewer's fourth finding above; two routes reached it independently.
- [ ] **README before the code** — the paragraph that conveys the idea gets written day one.
- [ ] **An architecture note for the frontend before its first story** — sprint 4 had none
      and said so.
- [ ] **Reviewer feedback as a backlog on day one** — this file. The only action from the
      previous retro that visibly changed behaviour.
- [ ] **Decide about mid-sprint feedback rather than carrying it** — book it or strike it. An
      item knowingly ignored teaches that the list is optional.
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
- [ ] **Contracts at public boundaries** — a standing habit, not an increment: be ready to say
      what each public service accepts, returns and promises. **Unticked by design**; an empty
      box reads as "still in force".
- [ ] **No way to remove a document or clear the store** *(finding #8)* — the sidebar lists
      sources with no chunk count, no removal and no clear. Memory clearing shipped; document
      removal did not.
- [ ] **The page's heading outline and its tablist** — `SourcePanel`'s `<h2>` is the React
      page's only heading, and the `role="tab"` buttons have no `aria-controls` and no
      `role="tabpanel"` to point at. Referred back deliberately in sprint 4: the fix decides
      the whole outline and the tab/panel wiring together, so it is one accessibility story
      with its own criterion.

### Deferred suggestions, recorded not scheduled

- [ ] **RAG evaluation set** (10–20 questions with expected sources) — the most useful of the
      four, and the capstone is marked on evaluation: "how did you measure success" is one of
      the six presentation points.
- [ ] **PostgreSQL + pgvector instead of Chroma** — an adapter swap behind the `Retriever`
      port. Cheap to do later; note that the reviewer's store finding above may decide it.
- [ ] **Second-stage semantic reranking** — a wider candidate set through a cross-encoder
      before context selection.
- [ ] **Richer chunk metadata** (headings, sections, page numbers, doc type) — what would make
      citations better than filenames. Revisit with the evaluation set.
