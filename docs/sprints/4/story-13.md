# Story 13: The package diagram is read off the imports

**As a** reviewer reading the architecture · **I want** one diagram of the packages and what
they depend on, built from the source · **So that** the layering I am told about is one I can
see, and it cannot drift from the code

> **Given** the seven distributions in the workspace
> **When** I open `docs/diagrams.md`
> **Then** I see one box per package with an arrow to each package it imports — and an import
> that changes without the diagram being rebuilt fails the suite

## The shape

`grimp` builds the import graph and squashes a package into a single node, which is the whole
diagram: eight boxes, eighteen arrows, about a dozen lines. It reads `cora` by name across all
seven `src` roots — namespace packages and all — so there is no tree to assemble, no synthetic
`__init__.py`, and no walker of our own. It is the library behind import-linter, so if the
layering guard ever moves off hand-written `ast`, the same graph serves both.

The graph is not taken on trust: aggregating `ast` imports independently during planning gave
the same eighteen arrows, and squashing turns a package's internal imports into self-loops,
which are dropped rather than drawn as a box pointing at itself.

**Not pyreverse.** `--max-depth` prunes rather than rolls up — at depth 1 it is eight boxes and
*zero* edges — so it cannot draw this picture at all, and its `-o mmd` names nodes by leaf,
merging `cora.app.retrieval` with `cora.ports.retrieval`. pyreverse is the next story's tool,
where classes are the subject and it is the right one.

The generator lands in `scripts/package_diagram.py` — it writes a docs artefact, so it is not a
test helper; `tools` joins pytest's `pythonpath` and ruff's and ty's roots. Output is a Mermaid
block, inline like every other diagram, so freshness is a string compare and nothing renders an
image.

**It does not replace the distributions diagram** in `big-picture.md`. That one's arrows are
declared dependencies — what you install — and these are imports. They differ on purpose: `cora`
depends on `cora-plugin-security` in its manifest and imports it nowhere.

## Test list

**Tiers:** unit throughout — `grimp` parses, it does not import.

#### First, the outer test

- [x] the Mermaid block regenerated from the workspace is identical to the one committed in
      `docs/diagrams.md` — `xfail(strict=True)` until the generator and the page exist.
      The seam had to exist for the gates: `ty` cannot resolve a module the test names, so the
      commit carries `scripts/package_diagram.py` raising `NotImplementedError` and the three
      config entries that put `tools` on pytest's, ruff's and ty's paths

#### Which boxes — the only judgement in the pipeline

- [x] a box per second-segment package, except the two extension points, which contribute their
      children instead: `cora.plugins.fitness` and `cora.plugins.security` are boxes and
      `cora.plugins` is not
- [x] the boxes are read off the graph, so a second frontend becomes a box with no edit here
- [x] the namespace root itself is no box

#### Squashing tells the truth

- [x] several modules crossing one boundary are one arrow
- [x] a package's internal imports are no arrow from a box to itself
- [x] a mutually dependent pair is drawn both ways rather than deduped — `cora.domain` and
      `cora.ports` are that pair today, and hiding half of it would make the picture a lie
- [x] a framework import is no box: the graph is built over `cora` alone

#### Mermaid that renders

- [x] node ids are the full dotted names, so two boxes sharing a leaf name stay two boxes — the
      trap pyreverse's own Mermaid output falls into
- [x] a box nothing imports and that imports nothing is still drawn *(discovered — without it
      a package joins the workspace and the diagram silently omits it)*
- [x] the block parses on Mermaid 10.2.3 — checked against a local `mermaid@10.2.3`
      `mermaid.parse`, which is where dotted node ids were confirmed legal. Not a committed
      test: it would put node in CI for one assertion about syntax that does not change

#### The two diagrams say different things

- [x] `cora` declares `cora-plugin-security` in its manifest and imports it in no module — the
      arrow the distributions diagram has and this one must not
- [x] `docs/big-picture.md` links the new page and says which diagram is manifests and which is
      imports — the link is a path, so `test_docs.py` fails the day the page moves
- [x] `make diagram` rewrites the block and leaves the prose around it *(discovered — the page
      is hand-written apart from the fence, so the command has to splice rather than write)*
- [x] `README.md` names the command and that the dev group is the whole prerequisite

## Out of scope

- **The class diagrams.** pyreverse's actual strength, and the next story: one run per `src`
  root, where none of this aggregation is needed. Expect `domain` and `ports` to be rich and
  `engine` sparse — it is mostly module-level callables.
- **Moving `test_architecture.py` onto grimp.** Its guards carry forbidden frameworks and a
  reason per layer; re-pointing them is a refactor of a passing suite, not this story.
- **graphviz, dot, or a committed image.** Mermaid is the whole output.
- **Reconciling every declared dependency against the imports.** One asymmetry is asserted,
  because the two diagrams disagree there on purpose.

## Dropped after the fact

The freshness test and every unit test of the generator were deleted at the author's request:
the diagram is regenerated by `make diagram` and nothing checks that the committed page is
current. The test list above records what was built and passing when
the story closed, not what guards it now.
