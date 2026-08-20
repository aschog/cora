# Story 26: a public name says what it promises

**As a** developer reading the reference · **I want** every public name to say what it
accepts, returns and promises · **So that** I learn the part the signature cannot show

> **Given** the reference story 25 generates
> **When** I open a page in `cora.domain`, `cora.ports`, `cora.engine` or `cora.app`
> **Then** every public name on it carries a docstring in Google's sections, stating what
> the annotation cannot — and ruff refuses a commit that adds a public name without one

**This retires the standing no-docstring rule** for those four packages, and rewrites the
*Settled, not per file* paragraph in `docs/workflow.md` to say what replaces it: a public
name in a rendered package carries a docstring, because an absent one is a blank page in a
reference someone opened on purpose. 174 of them — 60 in `domain`, 48 in `ports`, 56 in
`engine`, 10 in `app`. It stays retired only there: `adapters`, the plugins, the frontends
and the tests keep `D` ignored, and a docstring appears there only if it states something
the code can't.

What earns a section is what the type cannot carry — a unit, a constraint, an ownership
rule, and `Raises:`, which no annotation expresses at all. **`D417` stays off**: it demands
that an `Args:` block name every parameter, which forces `query: The query string.` beside
`query: str`, and that restatement is the one thing certain to drift out of sync.

`engine` is the package to be careful in. Its flows are already documented — `big-picture.md`
states `PrepareStep`'s rule ordering and ingestion's refusals under `agent.answer` and
`kb.add_file`, and `happy-path.md` draws the turn — so an engine docstring states what
*that name* promises,
never how a turn runs: `ToolRuntime.execute`'s swallow-versus-propagate rule,
`PluginSet.rules`' ordering, `ingestion.ingest`'s size and type limits. A docstring that
retells the sequence diagram is the duplication this project has always refused.

The rule arrives per package, by deleting a line from `per-file-ignores`, so the list is
the visible backlog and no gate is red waiting for the next package.

## Test list

**Tiers:** unit unless marked. The four items under *Package by package* are red→green
increments driven by `ruff check` rather than by pytest — the linter is the failing bar,
and the ignore line is what makes it fail.

#### The rule's edges, pinned so they cannot drift (fixture under `tests/guards/`)

- [ ] a public class in a rendered package with no docstring is reported
- [ ] the same class in `cora.adapters` is not — the ignore list is the boundary, and it is
      the backlog for what has not been taken
- [ ] a test function with no docstring is reported by nothing; test names carry the
      behaviour and no page renders them
- [ ] a docstring with an `Args:` section naming one parameter of three is *not* reported —
      `D417` is off, so documenting only the parameter whose meaning the type cannot carry
      is allowed
- [ ] a summary line running straight into its second sentence *is* reported in a rendered
      package, so a page does not open on a wall of prose
- [ ] the convention is read from `pyproject.toml`, not from a per-file directive — one
      place decides the format

#### Package by package (`ruff check` red until the package is done)

- [x] `cora.ports` — 48; taken first, because a Protocol's docstring is the only place its
      contract exists at all: `ty` checks conformance and no test spells it out
- [ ] `cora.domain` — 60; the types that cross to a frontend
- [ ] `cora.app` — 10; `build`, `App`, `Config`, `int_setting` — what a new frontend calls
- [ ] `cora.engine` — 56; per-name guarantees only, with the flows left to the narrative
      pages

#### What the reference shows once the prose exists

- [ ] **(int)** a `Raises:` section renders as a section, not as preformatted text — the one
      thing no annotation carries has to read as structure
- [ ] **(int)** an `Args:` section naming one parameter of three renders that one, and the
      other two still show their annotations from the signature
- [ ] **(int)** a `Protocol`'s page carries the ordering guarantee its docstring states —
      `Conversations.sessions` is newest first, and the page is where an implementer reads it

#### What the repo claims about itself

- [ ] `docs/workflow.md`'s path claims still resolve after the paragraph is rewritten —
      `test_docs.py` already reads that page
