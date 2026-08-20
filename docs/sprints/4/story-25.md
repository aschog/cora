# Story 25: one site — the map, the walkthrough and the reference

**As a** developer picking cora up · **I want** the map, the walkthrough and the contracts
under one nav · **So that** I look a type up in the same place I learned how a turn runs

> **Given** `docs/big-picture.md`, `docs/happy-path.md` and the four packages the reference
> covers
> **When** I build the site and open it
> **Then** the two narrative pages render with their five diagrams, and `cora.domain`,
> `cora.ports`, `cora.engine` and `cora.app` each have a page per module — and a module
> added later has one without anyone editing a nav

Two Diátaxis quadrants, one nav. *Explanation* stays written and stays where it is:
`big-picture.md` names every engine component to its file and states what `PrepareStep` and
`add_file` guarantee, `happy-path.md` draws the turn as a sequence. Neither can be derived
from source — the port map encodes which Protocol is a seam and why, the sequence encodes
an order of calls no import graph sees — which is why the diagrams stay hand-drawn Mermaid.
*Reference* is generated: `mkdocstrings` collects through Griffe, which reads source as an
AST rather than importing it, so the build loads no layer and
`tests/guards/test_architecture.py` has nothing to say about it. How-to stays in
`README.md`, which keeps its job as the repo's front door and links in; there is no
tutorial and nothing here needs one.

The ruff rule arrives in **story 26**, not here. Griffe renders signatures, annotations,
dataclass fields and inheritance from the code alone, so all 42 modules have a page the day
the site builds, and story 26's prose lands on pages already in place. Splitting them is
what lets this one merge as something you can open.

`adapters` is not in the reference: every public class in it implements a port, so its
methods *are* the port's methods, and a Protocol implementation inherits no docstring to
render — the prose would have to be copy-pasted from `ports/`.

**Out of scope.** Publishing: no Pages workflow, no `gh-pages`, no public URL. `griffe
check` as a break-detector — the only stable reference point is `v1.0.0`, which this sprint
has deliberately left behind, so it would report the intended rewrite as a wall of
breakage.

## Test list

**Tiers:** unit unless marked — **(int)** integration, because the step builds the site.

#### The outer test

- [ ] **(int)** the site builds strict-clean from the tree alone; both narrative pages are
      in it, and every module of `cora.domain`, `cora.ports`, `cora.engine` and `cora.app`
      has a reference page no one wrote by hand

#### The site holds what the repo has, and nothing else (`mkdocs.yml`, `docs/index.md`)

- [x] `docs/sprints/**` contributes no page — 52 files of build history are not the product
- [x] `docs/cora_mockup.html` and `docs/workflow.md` contribute none either: one is a
      mockup, the other documents the process rather than the product
- [x] both narrative pages are reachable from the nav
- [ ] `docs/index.md` links every top-level section, so the front page is not a dead end
- [x] the built site is not tracked; a generated tree in the repo would be reviewed as source

#### It reads with no network (`extra_javascript`, `theme.font`)

- [ ] no built page loads a script, stylesheet, font or image from another host — "built and
      read locally" has to mean it renders with the network off
- [ ] the vendored Mermaid is 10.2.3, the version the diagrams are written against
- [ ] all five Mermaid blocks across the two pages survive into the built HTML as diagram
      containers rather than as code blocks

#### One reference page per module, found rather than listed (`docs/api/`)

- [x] every module of the four packages has a generated page, read off the tree — the nav
      names the reference once and never a module, so one added later needs no edit to
      `mkdocs.yml`
- [x] a module whose name starts with `_` gets no page
- [x] `__init__.py` becomes the package's own page, not a page called `__init__`
- [x] `adapters`, `plugins/` and `frontends/` get no pages
- [x] a module's page is at `api/cora/<package>/<module>/`, so the built path is the dotted
      name
- [x] **(int)** the reference has a landing page listing every module
- [x] **(int)** no nav file is shipped as a page — literate-nav's implicit index makes the
      summary *be* that landing page, rather than a stray `SUMMARY` beside it

#### What a reference page carries with no docstring present

- [ ] **(int)** a frozen dataclass shows its fields with their annotations —
      `ToolResult.error` reads `str | None`
- [ ] **(int)** a class carrying no docstring still shows its signature and its fields, so
      the site is useful before story 26 lands
- [ ] **(int)** a `Protocol`'s methods show their signatures — `Retriever.query` is on the
      page
- [ ] **(int)** an error subclass shows what it inherits, so `errors.py` reads as one
      hierarchy rather than twenty unrelated classes

#### What the repo claims about itself

- [ ] a backticked `mkdocs.yml` in `README.md` resolves against the tree — `test_docs.py`
      reads `.py`, `.md`, `.toml` and directories, and the repo now has a `.yml` worth
      policing
- [ ] `docs/index.md` joins `test_docs.py`'s `PAGES`, so the front page's path claims are
      checked like every other current page
- [ ] `README.md` names the site and how to build it, beside the pages it already lists
