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

- [x] **(int)** the site builds strict-clean from the tree alone; both narrative pages are
      in it, and every module of `cora.domain`, `cora.ports`, `cora.engine` and `cora.app`
      has a reference page no one wrote by hand

#### The site holds what the repo has, and nothing else (`mkdocs.yml`, `docs/index.md`)

- [x] `docs/sprints/**` contributes no page — 52 files of build history are not the product
- [x] `docs/cora_mockup.html` and `docs/workflow.md` contribute none either: one is a
      mockup, the other documents the process rather than the product
- [x] both narrative pages are reachable from the nav
- [x] `docs/index.md` links every top-level section, so the front page is not a dead end
- [x] the built site is not tracked; a generated tree in the repo would be reviewed as source

#### It reads with no network (`extra_javascript`, `theme.font`)

- [x] no built page loads anything from another host, read with `html.parser` rather than a
      pattern. Two hand-written versions were narrower than their name: the first matched
      only `script src`, `img src` and `link href`, so an `iframe src` or `img srcset` went
      by; the second stopped reading a tag at its first boolean attribute, so
      `<script defer src=…>` and any single-quoted value went by. `a` is allow-listed as a
      link the reader follows, and the `content` exemption is gone — it bought nothing and
      would have exempted a real `og:image`
- [x] the vendored Mermaid is 10.2.3 — the version *inside* the bundle is checked against
      the one in its filename, because the first version read neither and a Mermaid 11
      bundle under the same name passed. Provenance sits beside the declaration
- [x] all five Mermaid blocks across the two pages survive into the built HTML as diagram
      containers rather than as code blocks
- [x] **(int)** every narrative page loads the vendored copy — Material falls back to
      fetching `mermaid@11` from unpkg when the global is missing, so loading ours is what
      makes the fallback inert. `extra_javascript` is site-wide, so the 42 reference pages
      carry it too without needing it

The guard reads what a *page* references. Material's own bundle carries two conditional
CDN fallbacks it cannot be configured out of — `mermaid@11` and a `ResizeObserver`
polyfill — so "no CDN string anywhere in the build" is not a claim any test here can make.
Both are guarded by a `typeof … == "undefined"` check, and the item above is what keeps the
first one from firing.

#### One reference page per module, found rather than listed (`docs/api/`)

- [x] every module of the four packages has a generated page, read off the tree — the nav
      names the reference once and never a module, so one added later needs no edit to
      `mkdocs.yml`
- [x] no page for anything private — every part below `cora`, not just the last: the walk
      is recursive, so a public module inside a `_private` package was reaching the site
- [x] a module inside a *public* subpackage does get one — the case that makes the
      recursion itself testable, and the outer test discovers the same way
- [x] `__init__.py` becomes the package's own page, not a page called `__init__`
- [x] `adapters`, `plugins/` and `frontends/` get no pages — all three, where the fixture
      had only held `adapters`
- [x] a module's page is at `api/cora/<package>/<module>/`, so the built path is the dotted
      name
- [x] **(int)** the reference has a landing page listing every module
- [x] **(int)** every module page is titled by its dotted name — mkdocs takes a title from
      the filename long before mkdocstrings renders one, so `<module>/index.md` made all 42
      pages `Index` in the tab, the sidebar and the search results. Front matter fixes it
- [x] **(int)** nothing in the search index is titled `Index`, counted over page titles
      only — an anchor document carries the mkdocstrings heading, so a module's dotted name
      is in the index whatever its page is titled, and that half held either way
- [x] **(int)** the landing page and the sidebar agree on one order, compared over whole
      module paths — literate-nav writes no nav file and infers the section in path order,
      so the landing page is written sorted to match. Two orders for one list was the tell
      that the nav file was never read. The first version of this guard captured only the
      segment after `cora/`, so it compared four package names for forty-two modules and
      reversing the per-module sort left it green
- [x] ~~no nav file is shipped as a page — literate-nav's implicit index makes the summary
      *be* that landing page~~ — **the mechanism was never running.** `implicit_index` is
      inert: with no `nav_file` present literate-nav globs the directory, and setting
      `nav_file: index.md` is not the fix either — it makes *every* `index.md` a nav file,
      including the site's front page, whose prose then fails the parser. The option is
      gone and the test that asserted no stray `SUMMARY` went with it: nothing writes one,
      so no mutation could red it. Found by the branch review

#### What a reference page carries with no docstring present

- [x] **(int)** a frozen dataclass shows its fields with their annotations —
      `ToolResult.error` reads `str | None`
- [x] **(int)** a class carrying no docstring still shows its annotated fields — `answer :
      str`, `citations : tuple[Citation, ...] = ()` — so the site is useful before story 26
      lands. Asserting the bare field *names* proved nothing: each is a contents entry too.
      The item said *signature* until the page was read: mkdocstrings renders no class
      signature for a frozen dataclass, only the `dataclass` label, the annotated
      attributes and a separate `__init__` member
- [x] **(int)** a `Protocol`'s methods show their signatures — `Retriever.query` is on the
      page
- [x] **(int)** an error subclass shows what it inherits — the pair `UnsupportedFileTypeError
      Bases: IngestionError`, not the two names, which are headings whatever the bases do
- [x] **(int)** the hierarchy reads in source order, asserted on three classes that invert
      under alphabetical ordering — the first three chosen did not, so the mutation passed
- [x] **(int)** all four are read off the *rendered* page, with the collapsed source block
      removed first — every definition's source is on the page, so an assertion that saw it
      would pass on any rendering at all

#### What the repo claims about itself

- [x] `docs/index.md` joins `test_docs.py`'s `PAGES`, so the front page's path claims are
      checked like every other current page
- [x] `README.md` names the site, `make docs`, `make docs-serve` and the script that
      generates the reference — and that last path is what the guard can hold
- [x] ~~a backticked `mkdocs.yml` in `README.md` resolves against the tree~~ — **not
      achievable, and the item was wrong.** `test_docs.py` matches a *path*: its regex
      requires a slash, so a bare filename is invisible to it whatever suffixes are
      listed. Adding `.yml` to `SUFFIXES` changed nothing and was reverted as dead config
      — the mutation that renamed `mkdocs.yml` in `README.md` stayed green, which is how
      this was found. `scripts/gen_reference.py` is the claim the guard does police, and
      renaming it reds the guard.

#### Found in use

- [x] `make docs-serve` does not want the app's port — the React shell defaults to
      `127.0.0.1:8000` and so does `mkdocs serve`, so reading the docs beside the running
      app needed one of them stopped. The docs take 8001, and the guard reads the app's
      `DEFAULT_PORT` rather than a copy of the number

#### Not on the list, and deliberately

`make docs` and `make docs-serve` have no test of their own: the targets are two lines over
`uv run mkdocs`, and the strict build they wrap is what the outer test already runs. A test
asserting a Makefile line exists would pin the wrapper, not the behaviour.
