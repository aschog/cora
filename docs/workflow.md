# Project Workflow

A generalized, stack-agnostic workflow for starting projects and building features
with AI assistance. The TDD loop is driven by **human + AI together** — the AI is a
pair partner, not an autopilot. Placeholders like `<test runner>` get filled per
project. Every phase should be an atomic commit.

---

## Phase 0 — Project setup (once per project)

- [ ] Define the stack: language(s), framework, key libraries, package manager
- [ ] Bootstrap the repo: init git, `.gitignore`, project scaffold, `README.md`
- [ ] Set up the toolchain: formatter, linter, type checker, `<test runner>`
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
- [ ] Write down requirements / acceptance criteria (what "done" means)
- [ ] **Research unknowns** with `ai-researcher` (libraries, APIs, prior art) —
      before planning, not during coding
- [ ] Draft a plan with `ai-architect` from the requirements + research
- [ ] **Refine the plan into a TDD checklist**: decompose it so that every item is
      one failing-test-sized increment — if it can't be phrased as "write a test
      that shows X", split it
- [ ] Save the checklist as `docs/plans/<feature>.md` and commit it to the branch

---

## Phase 2 — TDD loop (repeat until checklist is done)

- [ ] Pick the next unchecked item from `docs/plans/<feature>.md`
- [ ] **Red** — write a failing test; run it and *see it fail* for the right reason
- [ ] **Green** — write the minimal code to make it pass; all tests green
- [ ] **Refactor** — clean up code *and tests*; stay green
- [ ] **Auto-commit** the green step (Conventional Commit message; hooks enforce green)
      — messages must read as a **history**: the commit log of a branch tells the
      story of the feature growing, each message says *what* changed and *why*
- [ ] **Update the checklist**: tick the item; add any newly discovered items or
      scope changes — the plan is a living document
- [ ] Repeat — but if an increment reveals the plan itself is wrong, stop and
      **re-plan** (back to Phase 1 with `ai-architect`); don't improvise off-checklist

> Every green step is a save point. If a cycle goes sideways, reset to the last
> green commit instead of untangling a big diff.

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
- [ ] All checklist items in `docs/plans/<feature>.md` ticked
- [ ] Update project docs the feature touched (`README`, `CLAUDE.md`, `docs/`)
- [ ] **Merge manually** into trunk as **one atomic commit** — squash the
      micro-commits so trunk history reads one green, self-contained commit
      per feature
- [ ] **Keep the feature branch** (don't delete) — the micro-commit trail stays
      publicly visible as evidence of the TDD process
- [ ] Mark the plan as done by moving it into `docs/plans/done/`
