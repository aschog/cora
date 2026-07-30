# No startup seeding

Deleting `.cora/chroma` and restarting brings the hardcoded seed docs
(`protein.md`, `energy_balance.md`) back: `assemble()` re-ingests
`plugin.seed_docs` on every launch (`assembly.py:77-78`), so the real app never
starts empty. Stop the production app from seeding, but keep the seeding
mechanism so tests can still exercise it.

## Acceptance criteria

- The running app (`build()`) ingests **no** seed docs at startup — the store
  starts empty (deleting `.cora/chroma` and relaunching leaves it empty).
- `assemble()` can still seed, so the plugin `seed_docs` field and the existing
  seeding unit tests stay unchanged.
- `Plugin.seed_docs` and `fitness.SEED_DOCS` stay (used by tests).

## Design

- Add `seed: bool = True` to `assemble()`; guard the seed loop with it.
- `build()` passes `seed=False`.
- No other production caller of `assemble()` exists, so nothing else seeds.

## TDD checklist

- [x] `assemble(..., seed=False)` leaves the retriever's sources empty though the
      plugin carries seed docs. Green: add the flag + guard.
- [x] `build()` starts with an empty store (no `protein.md` in sources).
- [x] Reframe e2e `test_a_page_load_ingests_the_seed_docs...` → a fresh page
      loads with **no** documents in the sidebar.
- [x] Rewrite integration `test_build_rehydrates_hybrid...` to populate via
      `add_file` instead of seeding, keeping the restart/dedupe assertion.

## Fallout

- `big-picture.md` says the composition root "seeds its documents" — update to
  reflect that startup no longer seeds.
