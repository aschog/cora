# Story 9: The layout says what the architecture is

**As a** developer meeting this codebase · **I want** the folder names to name the layers ·
**So that** I can read the architecture off `ls` instead of inferring it from imports

> **Given** the repository root
> **When** I list it without opening a file
> **Then** I see the domain, the service layer, the ports, the adapters and the
> entrypoints as separate named things — and each ships as a package that declares only
> the dependencies its layer is allowed

A structural refactor, not a feature: no user-facing behaviour changes, and the app must
run and answer identically at every step. It maps to no assignment requirement, so it
carries no bonus — it exists to make the hexagon legible and to make "core is pure" a fact
of the packaging rather than a rule a test polices.

## The shape

Four distributions in a `uv` workspace, sharing the `cora.` namespace:

```
packages/cora-core/      domain · service_layer · ports        deps: jsonschema
packages/cora-adapters/  chroma · openrouter · langgraph · bm25 · st · loaders
packages/cora-fitness/   the reference plugin                  deps: cora-core
packages/cora-app/       bootstrap · config · entrypoints/      deps: all three
```

Proven by spike before planning: `uv_build` builds namespace packages with
`module-name = "cora.core"` and `namespace = true`; `cora.app` → `cora.adapters` →
`cora.core` imports resolve across distributions; and `cora-core` installed alone brings
`jsonschema` and no `chromadb`.

**Packaging and renaming are independent.** Splitting the distributions changes no import
statement, because `cora.core` stays `cora.core`. Only the layer rename moves module paths.
They are separate commits so each can be verified alone.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.
**(moved)** marks a test that relocates rather than a new one.

#### First, a net for the move

- [x] **(llm)** the live acceptance runs over `AppTest` instead of a browser: a plain
      training question answers with a citation and a greeting beside it cites nothing —
      the one check that exercises the assembled stack end to end, and the move's only
      cover against a wiring mistake no unit test would see

#### The workspace holds four packages

- [x] each package's tests sit beside it, and the shared fakes stay at the root — nothing
      under `tests/` may be named for a shipped module, or it joins the `cora` namespace as
      its first portion and shadows the real one
- [ ] a package's tests run against that package installed alone — needs the shared fakes
      to stop being a root-level import first, so it is deferred, not done
- [x] `cora-core` imports with neither `chromadb`, `langgraph`, `sentence_transformers`,
      `streamlit` nor `rank_bm25` importable — the purity `test_architecture.py` asserts,
      now enforced by what the distribution installs
- [x] `cora-fitness` imports with only `cora-core` present, so a plugin author needs none
      of the adapter stack
- [ ] the loaders move to `cora-adapters`: a PDF reader is a driven adapter over a file
      format, and it is the only reason `pypdf` sat in core
- [ ] `config` no longer reads a constant out of an adapter — it owns its own default, so
      the app package does not depend on an adapter for a string

#### The layers are named

- [ ] `cora.core.domain` holds what the problem is made of, `cora.core.service_layer` the
      use cases, and every test still finds them *(moved)*
- [ ] a domain module may not import the service layer — the guard the shared package still
      needs, since siblings inside one distribution are not separated by metadata
- [ ] `cora.app.entrypoints` holds the Streamlit app, so a second entrypoint has an
      obvious home *(moved)*
- [ ] `ContextSource` moves into `core.ports`, so "ports live in `ports/`" is true without
      exception
- [x] `test_architecture.py` walks all four package roots and still fails on a planted
      violation — rooted at one package it silently stopped covering the other three

#### Nothing changed but the shape

- [x] every change in the suite count is accounted for: 650 to 653 — the two namespace
      `__init__.py` files gone from four parametrised guards (-4), the smoke test split in
      two (+1), and the packaging manifests pinned (+6)
- [ ] **(int)** the app assembles and answers a document question through the composition
      root, exactly as before
- [ ] the pre-commit hook and CI run from the workspace root and gate every package
- [ ] `README.md` and `big-picture.md` describe the packages, and the package-structure
      diagram is redrawn

## Order

1. the `AppTest` acceptance net — before anything moves
2. the four distributions, no import edits
3. the layer rename, all import edits
4. docs and diagram

Steps 2 and 3 are each one atomic commit: a half-migrated layout cannot be green.

## Out of scope

- Publishing to an index. The workspace is for development; nothing is released.
- Splitting adapters per technology. One `cora-adapters` until a second consumer wants less.
- Test-per-package directories beyond what step 2 needs — cross-cutting suites and
  `test_architecture.py` stay at the root, where they already belong.
