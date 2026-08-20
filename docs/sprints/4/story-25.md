# Story 25: the contract is read off the code

**As a** developer picking cora up · **I want** the domain and the ports as a browsable
reference · **So that** I read what a type promises without opening eleven modules to
find out

> **Given** `cora.domain` and `cora.ports` as they stand
> **When** I build the reference and open it
> **Then** every module of both has a page carrying its types, its fields and the errors
> it inherits — and a module added later has one without anyone editing a nav

The reference is generated, never written: `mkdocstrings` collects through Griffe, which
reads source as an AST rather than importing it, so the docs never load the layers and
the purity guard in `tests/guards/test_architecture.py` has nothing to say about them.
That is also what makes the story possible under the standing no-docstring rule —
annotations, dataclass fields and the `CoreError` hierarchy are the contract for these two
packages, and a page is not empty without prose. Google's docstring *sections* become a
lint rule for the docstrings that do exist; none is required. Built locally with
`make docs` and read with `make docs-serve`; the strict build is an integration-marked
guard, so CI runs it as part of `integration-tier` and needs no step of its own.

**Out of scope.** Publishing — no Pages workflow, no `gh-pages`, no public URL. And
`engine`, `adapters` and `app`: they are how cora works, not what it promises. `griffe
check` was considered as a break-detector and dropped: the only stable reference point in
the tree is `v1.0.0`, which the sprint has deliberately left far behind, so the check
would report this sprint's intended rewrite as a wall of breakage. A guard that fails on
every change made on purpose is noise.

## Test list

**Tiers:** unit unless marked — **(int)** integration, because the step builds the site.

#### The outer test

- [ ] **(int)** the reference builds strict-clean from the tree alone, and every public
      name `cora.domain` and `cora.ports` export is on a page — no module's page is
      written by hand

#### One page per module, found rather than listed (`docs/api/`, `mkdocs.yml`)

- [ ] every module of both packages has a generated page, read off the tree — a module
      added later needs no edit to `mkdocs.yml`
- [ ] a module whose name starts with `_` gets no page
- [ ] `__init__.py` becomes the package's own page, not a page called `__init__`
- [ ] a package under `plugins/` or `frontends/` gets no page — the reference is the app's
      contract, not every distribution's surface
- [ ] the built site is not tracked; a generated tree read as source would be reviewed as
      source

#### What a page has to carry

- [ ] **(int)** a frozen dataclass shows its fields with their annotations —
      `ToolResult.error` reads `str | None`
- [ ] **(int)** a class carrying no docstring still shows its signature and its fields, so
      the policy leaves no empty page behind
- [ ] **(int)** a `Protocol`'s methods show their signatures — `Retriever.query` is the
      contract and it is on the page
- [ ] **(int)** an error subclass shows what it inherits, so `errors.py` reads as one
      hierarchy rather than twenty unrelated classes
- [ ] **(int)** the class docstring `Documents` already carries is rendered — the
      invariants that *are* written are the ones a reader came for

#### The docstrings that exist keep their form (ruff `D`, Google convention)

- [ ] a docstring with an `Args:` section that omits a parameter is reported
- [ ] a public class with no docstring at all is reported by nothing — `D1xx` stays off,
      so nothing about the standing policy changes
- [ ] a docstring whose summary runs straight into its second sentence is reported by
      nothing — `D205` and `D209` stay off deliberately, so turning the convention on
      cannot reformat fifty-nine docstrings that were written the way the house writes
      them
- [ ] the five `D` findings outside `src/` — two `D403`, one each of `D202`, `D210`,
      `D301` — are gone, so the rule turns on for the whole workspace rather than for two
      packages

#### What the repo claims about itself

- [ ] a backticked `mkdocs.yml` in `README.md` resolves against the tree — `test_docs.py`
      reads `.py`, `.md`, `.toml` and directories, and the repo now has a `.yml` worth
      policing
- [ ] `README.md` names the reference and how to build it, beside the four pages it
      already lists
