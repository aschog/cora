## Context

The folder scan in `cora.engine.plugin_registry` globs `*.py` files once at startup,
and the React API closes over that one assembled `App` for the process's life.

## Goals / Non-Goals

- Goal: a dropped package loads through the same checks a dropped file passes.
- Goal: relative imports inside the package resolve without the author changing them.
- Goal: the folder is the truth while serving — drop installs, delete removes, edit
  reloads.
- Non-goal: installing a package's dependencies — a missing import is a refusal.
- Non-goal: nested plugin folders, manifests, watchers, or any packaging metadata.
- Non-goal: reloading plugins named in `CORA_PLUGINS` — modules stay as started.

## Decisions

### Packages in the folder

- The seam is the loader's discovery step: the folder scan yields packages beside
  files, and one shared load path takes both.
- A package is a directory holding `__init__.py`; any other directory is ignored,
  as non-`.py` files already are.
- A package imports under `cora_dropped.<name>`, the namespace dropped files use, so
  no folder shadows an installed module.
- The spec's `submodule_search_locations` is the folder itself, which is what makes
  `from . import sibling` resolve.
- Loading registers the package in `sys.modules` before executing it, and restores
  what it displaced on failure — the discipline `load_file` already has.
- Submodules imported under the package's name are cleaned out on failure too, so a
  half-imported package leaves nothing behind.
- The folder's name faces every existing check unchanged: identifier, collision with
  named modules, cora's own name, contract version, `extend` present and callable.
- Hidden and underscore-led directories are skipped by the same rule that skips
  such files.

### The live folder

- The seam is `build`'s two halves pulled apart: adapters are made once for the
  process, and composition over them becomes repeatable.
- A holder in `cora.app` owns the current `App` plus the folder signature — every
  entry's name, kind and mtime — it was composed from.
- The API takes that holder instead of an `App`: each handler reads the current app
  once, so a turn runs whole on one set.
- A signature check is a directory stat, cheap enough to run per request; recompose
  only when it differs. <!-- ponytail: per-request stat scan, a watcher if folders grow huge -->
- Recomposition swaps under a lock, one at a time; readers keep whatever app they
  already took.
- Editing a dropped plugin re-executes its module: the `cora_dropped` names are
  replaced on recompose, and the old app keeps its old module objects.
- A folder state that refuses to load leaves the held app in place; the refusal
  answers that request as a `CoreError` already does, and is retried on the next.
- Named modules are loaded once at startup and passed into every recomposition
  untouched.
- A field has one rule: it is offered if anything brings it — a registration of any
  loaded plugin, or `CORA_SCOPES`, which stays only for fields no plugin registers
  (a documents-only field). Loading is the deployment act, however a plugin arrived.
- Symlinks are followed as the filesystem follows them: discovery, loading and the
  signature all stat through, so a linked package edits live.
- The app carries the fields it offers, and the api reads them off the current
  composition per request — its startup `scopes` parameter goes.
- Nothing tells named from dropped any more: the union reads every registration, so
  the named-first order stops carrying meaning and the compose seam takes one
  argument again.

## Risks / Trade-offs

- [A package's failing import blames a submodule deep inside it] → the refusal names
  the folder and carries the original exception, as file refusals do.
- [Two dropped plugins, `interview.py` and `interview/`, collide] → the existing
  same-name refusal already fires, since both carry the stem.
- [An edited plugin's old code holds state a new turn expects] → conversation state
  lives in cora's stores, not the module, so a recompose loses nothing kept.
- [mtime granularity misses a same-second edit] → signature includes size and every
  member file of a package, and a page reload a second later catches it.

## Migration Plan

None — deployments that never touch the folder compose once and serve exactly as
before.
