# Story 10: One core, many frontends, many plugins

**As a** developer extending cora · **I want** to write a plugin or a second frontend against
a package carrying only what that job needs · **So that** neither one drags in the other's
technology

> **Given** the workspace's distributions
> **When** I install `cora-fitness` on its own, and `cora` on its own
> **Then** the plugin resolves with no engine and no framework present, and the backend
> resolves with no Streamlit — so a further plugin and a further frontend each cost one
> package, and the app still answers exactly as before

A structural refactor: no user-facing behaviour changes. It maps to no assignment
requirement and carries no bonus. Story 9 made the layers legible; this makes the two
extension points real rather than described, by giving each audience a distribution it can
install alone.

## The shape

```
cora-api        cora.domain · cora.ports                  nothing — stdlib only
cora-engine     cora.engine                               → cora-api + jsonschema
cora-adapters   cora.adapters                             → cora-api + the five technologies
cora            cora.app — assembly · config · retrieval   → cora-engine · cora-adapters
cora-fitness    cora.plugins.fitness                      → cora-api
cora-streamlit  cora.frontends.streamlit                  → cora
```

- **The audience picks the split**, not the architecture diagram: a plugin author installs
  the contract, a frontend author installs the backend, and neither can reach what it was
  not given.
- **`core` stops naming a distribution**, so `cora.core.domain` becomes `cora.domain`. The
  segment goes because nothing is left for it to name — not as a rename argued on its own.
- **Two extension points, both plural**: `cora.plugins.*` and `cora.frontends.*`.
- `DONE`, `TOOLS` and `GROUND` move to `ports/graph.py` beside `GraphRunner`. They are the
  vocabulary a runner switches on, and being in `service_layer/steps.py` is the only reason
  an adapter needs the engine at all.
- The composition root keeps the name `cora.app` and does not move. Only `entrypoints/`
  leaves.
- `cora-api` carries two contracts at once: the four names a plugin uses, and the ports plus
  `AgentState`, `Chunk` and `MetadataFilter` an adapter needs. Splitting them again would
  make seven distributions for one reader's convenience, so they stay together — but the
  whole of `cora-api` is not the plugin API.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.
**(moved)** marks a test that relocates rather than a new one.

#### First, the outer test — the boundary as an install

- [x] **(int)** every distribution's wheel builds, and each module its manifest names
      imports from that wheel in a clean venv — nothing builds a wheel today, so
      `module-name` is unverified data and a mis-declared module ships as nothing
- [x] **(int)** `cora-fitness` installed alone imports, with `cora.engine` absent — the
      cheap install, and the one that carries the story
- [x] `streamlit` is absent from `cora`'s resolved dependency graph, and `cora-engine` from
      `cora-fitness`'s — asked of the resolver rather than of TOML, so it is transitive, and
      without installing chromadb and torch to learn it
- [x] `cora-api` resolves to itself alone: no third-party dependency at all — `jsonschema`
      belongs to the engine, which *checks* schemas; the contract only says a tool has one

#### The contract has a name of its own

- [x] `cora.domain` and `cora.ports` import with `cora.engine` absent — the domain-may-not-
      import-the-service-layer rule stops being a walker's rule and becomes a fact of the
      install, and its AST guard is deleted rather than moved
- [x] the fitness plugin's imports resolve against `cora-api` alone: `Plugin`, `Tool`,
      `ToolRefusal`, `InputRejectedError` — the four names it actually uses
- [x] every module each manifest names exists on disk, loose `.py` files included — a
      list-valued `module-name` ships only what it names, and the editable install never
      consults it

#### The adapters bind the contract, not the engine

- [x] the router reads `DONE`, `TOOLS` and `GROUND` from `cora.ports.graph`, and
      `LangGraphRunner` imports them from there *(moved)*
- [x] no `cora.adapters` module imports `cora.engine`
- [x] no `cora.adapters` module imports `cora.app` or any frontend — an adapter reusable by
      every frontend, which nothing enforces today

#### Five ports, five slots

- [x] `assemble` takes its `GraphRunner` as an argument like the other four ports — today it
      builds a `LangGraphRunner` itself, so the one port whose technology cannot be changed
      without editing the composition root is the one the map calls a slot
- [x] the logging wrappers live in the engine: they decorate ports and import no technology,
      so shipping them with Chroma and LangGraph misfiles them *(moved)*
- [x] a graph factory handed to `assemble` runs the turn, and `assemble` builds no runner
      of its own — replaces "assembly imports with cora.adapters absent", which turned out
      to be reachable only by deferring imports to fake a property the slot itself states
      honestly; `cora` ships the default wiring and depends on the adapters by design

#### The frontend is one of many

- [x] `cora.frontends.streamlit` holds the Streamlit app and its helpers *(moved)*
- [x] `cora.app` imports no frontend, so the backend assembles with none installed
- [x] `streamlit` is imported nowhere outside `cora.frontends.*` *(moved — re-points the
      existing guard off `cora/app/entrypoints`)*

#### The walker, smaller

- [x] one planted module carrying a framework import, an outer-layer import and a `pytest`
      import is caught on all three counts — replacing eight self-tests of the detectors,
      which is the part that rotted: three still name `core/services`, a directory gone two
      commits before this story
- [x] the forbidden-layer walk covers every shipped layer, not core files alone, and still
      fails on a planted violation in an adapter

#### Nothing changed but the shape

- [x] every test that named `cora.core.*` finds its module under the new path *(moved)*
- [x] each layer's `py.typed` still sits inside the module its manifest names, six
      distributions now *(moved)*
- [x] every change in the suite count is accounted for: 678 collected to 718, diffed by
      test *name* against the pre-story commit so a test that merely moved package does not
      read as one lost. 24 cases gone — the ten domain-import guards and their self-test,
      five detector self-tests, and eight renames — against 66 new, of which 46 are the
      cross-layer walk now covering the adapters and the app as well as the pure set. Two
      parametrised walks each lost one case, `cora/core/__init__.py` having ceased to exist
- [x] **(int)** the app assembles and answers a document question through the composition
      root, exactly as before
- [x] **(llm)** the live acceptance answers a training question with a citation, through the
      moved frontend *(moved)*
- [x] every location the docs claim resolves, and `big-picture.md` names the six
      distributions and both extension points

## Order

1. the isolated-install checks — red first, and they stay red until the split lands
2. `cora-api` out of `cora-core`: the contract gets its own distribution
3. the router outcomes move to `ports/graph.py`, so adapters stop needing the engine
4. `cora-engine` out of `cora-core`; `core` ceases to name anything and the paths flatten
5. `entrypoints/` leaves for `cora-streamlit`; the root keeps `cora.app`, its dist becomes `cora`
6. the walker shrinks
7. docs and diagram

Steps 2 to 5 are each one atomic commit: a half-migrated namespace cannot be green.

## Out of scope

- Publishing to an index. The workspace is for development.
- The second frontend and the second plugin themselves. This story makes each one cost a
  single package; it does not write them.
- Splitting adapters per technology. One `cora-adapters` until a second consumer wants less.
- A `cora` meta-distribution for convenience installs. There is no index to install from.
