# Project Workflow

A generalized, stack-agnostic workflow for starting projects and building features
with AI assistance. It distils the core **Extreme Programming (XP)** practices —
test-driven development, pair programming, continuous integration, small releases
and relentless refactoring. The TDD loop is driven by **human + AI together** — the
AI is a pair partner, not an autopilot. Every phase should be an atomic commit.

---

## Where the docs live

Everything about a sprint lives in `docs/sprints/<n>/`:

```
docs/sprints/4/
  assignment.md           the brief, verbatim
  spec.md                 the story cut, requirement coverage, out of scope
  sprint-4-feedback.md    last review's findings, as a tracked backlog
  story-01.md             one file per story: the story + its test list
  done/                   story files whose test list is fully ticked
  retrospective.md        written at sprint close
```

- **Planning reads the current sprint only.** The folder of the sprint in flight is the
  whole input. Earlier sprint folders are history: `docs/sprints/3/plans/done/` records
  how that code was *built*, not how it works today, so it is not consulted when
  planning. Only `workflow.md` and `big-picture.md` sit outside a sprint folder — they
  describe the project, not a sprint.
- **`story-NN.md` is the planning artefact**: the story (*As a · I want · So that* with
  its *Given/When/Then*) followed by a **test list**. `docs/sprints/4/done/story-01.md` is the
  current reference shape — match it.
- **A story lives in exactly one place.** When it gets its own `story-NN.md`, its text
  moves there and `spec.md` keeps only its heading, linked to the story file, so the
  story cut still reads in order and no criterion is stated twice.
- **The test list is Beck's, not a work breakdown** — every item is one failing test.
  It is expected to change as you go: add items as they surface, and if an item can't be
  phrased as "write a test that shows X", it does not belong on the list.

---

## Sprint preparation

- [ ] **Day one — read the assignment**, then cut it into stories with acceptance
      criteria. Anything that maps to no story is out of scope. The criteria come
      *with* the story, not after it:

  > **As a** researcher · **I want** to ask a question about my uploaded papers ·
  > **So that** I get an answer with citations I can verify
  >
  > **Given** a paper on BM25 has been indexed · **When** I ask "How does BM25
  > handle term saturation?" · **Then** I receive an answer citing that paper

- [ ] **Day one — turn the last review's findings into a backlog**: each one becomes
      a tracked checklist item in `docs/sprints/<n>/sprint-<n>-feedback.md`, so feedback
      is "tracked and ticked" instead of "in my head"

- [ ] **Give each story in flight its own `story-NN.md`**, numbered in merge order, and
      move it out of `spec.md` as you do

---

## Phase 0 — Project setup (once per project)

- [ ] Define the stack: language(s), framework, key libraries, package manager
- [ ] Bootstrap the repo: init git, `.gitignore`, project scaffold, `README.md`
- [ ] Set up the toolchain: formatter, linter, type checker, test runner
- [ ] Add a test **watch mode** command (fast unit layer reruns on every save)
- [ ] Install git hooks: pre-commit (format + tests), commit-msg (Conventional Commits)
- [ ] Set up CI mirroring the hooks (format check, lint, type check, tests)
- [ ] Write `CLAUDE.md`: commands + architecture rules (business logic in pure,
      unit-testable modules; thin UI/shell on top)
- [ ] Install AI **skills** matching the stack (toolchain plugins, framework docs)
- [ ] Define AI **subagents** in `.claude/agents/`:
  - [ ] `ai-architect` — turns requirements into plans; weighs trade-offs
  - [ ] `ai-code-reviewer` — reviews branch diffs for correctness, design, tests
  - [ ] `ai-researcher` — investigates unknowns, libraries, APIs during planning

---

## Phase 1 — Plan a feature

- [ ] Create a feature branch
- [ ] **Research unknowns** with `ai-researcher` (libraries, APIs, prior art) —
      before planning, not during coding
- [ ] Draft a plan with `ai-architect` from the story + research
- [ ] **Write the outer functional test** — one failing test per slice, straight
      from the acceptance criterion. Written up front it catches design mistakes a
      retrofitted test can't, and it is what stops out-of-scope work: no story, no
      outer test, no code. Mark it `@pytest.mark.xfail(strict=True)` (or a `wip`
      marker) so CI stays green while the slice is in progress
- [ ] **Refine the plan into a test list**: decompose it so that every item is
      one failing-test-sized increment — if it can't be phrased as "write a test
      that shows X", split it
- [ ] Write the test list into the story's `docs/sprints/<n>/story-NN.md`, under the
      story it serves, and commit it to the branch. The design rationale behind it does
      **not** go in the file — it belongs in the conversation, the commit messages and
      the tests

---

## Phase 2 — TDD double loop (repeat until the outer test is green)

The outer test from Phase 1 stays red and defines "done". The unit loop runs
*inside* it — you stop when it goes green, not when the test list looks finished.
The same red-green cycle covers bug fixes (reproduce first) and characterizing
legacy code.

```
write failing functional test   ←── outer loop (feature)
        │
        ├─ write failing unit test   ←── inner loop (design)
        ├─ make it pass
        ├─ refactor
        └─ repeat until…
        │
functional test goes green  →  feature done
```

- [ ] Pick the next unchecked item from the story's test list in
      `docs/sprints/<n>/story-NN.md`
- [ ] **Red** — write a failing test; run it and *see it fail* for the right reason
- [ ] **Green** — write the minimal code to make it pass; all tests green
- [ ] **Refactor** — clean up code *and tests*; stay green
- [ ] **Explain back** — before approving, I say in my own words what the diff does
      and why. If I can't, it doesn't get committed: read it, or have it walked
      through, until I can. **No commit I can't defend** — this is the checkpoint
      that keeps generated code from becoming unread code
- [ ] **Auto-commit** the green step after human has approved it (Conventional Commit message; hooks enforce green)
      — messages must read as a **history**: the commit log of a branch tells the
      story of the feature growing, each message says *what* changed and *why*
- [ ] **Update the test list**: tick the item; add any newly discovered items or
      scope changes — the list is a living document
- [ ] Repeat — but if an increment reveals the plan itself is wrong, stop and
      **re-plan** (back to Phase 1 with `ai-architect`); don't improvise off-list
- [ ] When the test list is done, **drop the outer test's `xfail` marker and watch it
      pass**. Still red means the slice isn't finished, whatever the list says

> Every green step is a save point. If a cycle goes sideways, reset to the last
> green commit instead of untangling a big diff.

> Tests follow the **Detroit (classicist) school**: drive behaviour through the
> public API with real objects and hand-written fakes, and assert on resulting
> **state**, not on how collaborators were called. Reserve stubs for true
> boundaries — network, models, nondeterminism.

> **A failing test is never the thing that gets fixed.** The AI does not edit,
> weaken or delete a red test to make the bar go green — the test is the spec, the
> production code is what moves. Watching the intermediate steps is how you catch it.

> **Settled, not per file.** Docstrings and comments are extra effort to keep in
> sync and appear **only if needed**: write none unless they state a contract the
> code can't express — names + tests are the source of truth. This is decided;
> don't relitigate it file by file.

> Don't narrate the diff — the reviewer reads it. After a step, say only what the
> diff can't show: a decision, a surprise, anything urgent or important. Silence
> on the mechanics is the default.

---

## Phase 3 — Review (before merge)

- [ ] Push the branch and **open a PR** — backs up the local auto-commits and
      kicks off CI; the PR is the review vehicle (diff, CI status, discussion)
- [ ] Run `ai-code-reviewer` on the **accumulated branch diff** (not single commits)
- [ ] **Human review** of the PR — the AI review is input, not a substitute; a
      person signs off on the diff before it can merge
- [ ] **Fix every finding** (AI or human) — route each fix back through the Phase 2
      TDD loop (test first, if the finding is behavioral); nothing merges as "TODO later"
- [ ] Re-run the review until it comes back clean and **CI is green on the PR**

---

## Phase 4 — Merge (manual, human decision)

- [ ] **Run the feature for real** and check it against the Phase 1 acceptance
      criteria — green tests alone don't prove the feature works
- [ ] Final sanity check: format, lint, type check, full test suite — and CI green
- [ ] Every item in the story's test list ticked
- [ ] Update project docs the feature touched (`README`, `CLAUDE.md`, `docs/`)
- [ ] **Merge manually** into trunk as **one atomic commit** — squash the
      micro-commits so trunk history reads one green, self-contained commit
      per feature
- [ ] **Keep the feature branch** (don't delete) — the micro-commit trail stays
      publicly visible as evidence of the TDD process
- [ ] **A fully ticked `story-NN.md`** is moved into `docs/sprints/<n>/done/`

---

## Phase 5 — Sprint close (once per sprint)

- [ ] **Tag the reviewed commit on trunk** — the sprint's submitted state gets a
      permanent name, so "the version the reviewer saw" survives every later
      merge:

  ```bash
  git tag -a v1.0.0 <commit> -m "Sprint 3 submission — cora RAG chatbot

  <one paragraph: what shipped, review date and outcome>"
  git push origin v1.0.0
  ```

  - **Annotated (`-a`), never lightweight** — an annotated tag is a real object
    carrying tagger, date and message, so it records provenance and
    `git describe` can anchor later work to it. A lightweight tag is a bare
    pointer with none of that. Use `-s` instead of `-a` once commit signing is
    set up.
  - **Semantic name** — `v1.0.0` for the first reviewed release; a sprint that
    reshapes the app is the next major. Sprint names don't order or compare, so
    the *message* says which sprint, not the tag.
  - **Name the commit explicitly.** Tags default to `HEAD`, which is usually a
    working branch by the time the sprint closes — pass the trunk commit that
    was actually reviewed.
  - **Push the tag on its own.** Tags do not travel with a normal `git push`.
  - No GitHub Release: the tag is the marker, and a release adds a second thing
    to keep true.
