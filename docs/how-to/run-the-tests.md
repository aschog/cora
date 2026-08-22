# Run the tests

Five tiers, cheapest first. The unit tier is the one that runs on every save.

```sh
uv run ptw .                  # test watch mode (unit tier, reruns on save)
uv run pytest                 # unit tests (default; fast, no network/models/UI)
uv run pytest -m integration  # integration tier (real Chroma, embeddings, Streamlit)
uv run --env-file .env pytest -m llm   # live acceptance: real OpenRouter round-trip, costs tokens
uv run ruff format .          # format
uv run ruff check .           # lint
uv run ty check               # type check
make ui-test                  # the React page's own tier (vitest over happy-dom)
make ui-test-browser          # the browser tier (vitest over real Chromium; opt-in)
```

No browser is needed for any *local* gate: the Streamlit UI is driven headlessly through
its `AppTest`, including the live tier, and the React page through `happy-dom`. The React
tier is the one gate that needs node, which is why the pre-commit hook does not run it.

One tier does need a browser, and CI is where it gates: the pre-commit hook leaves it out
and so does `npm test`. Two things are invisible to happy-dom. What the reader keeps while
an answer is being written — a selection inside the paragraph still growing — survives or
collapses identically there, because it moves no selection boundary when a text node is
rewritten. And it applies no stylesheet, so what colour the page actually draws a cited
passage in cannot be read from it at all. `make ui-test-browser` asserts both in Chromium;
locally that needs `npx playwright install chromium --only-shell` once.

The `llm` tier is the only one that spends money. It runs the whole shipped stack —
the composition root, a real Chroma store and embedder, and OpenRouter over the
network — against the assembled page, because a scripted model answers however the
script says and so can never show the real one ignoring an instruction. It needs
`OPENROUTER_API_KEY` (here via `--env-file .env`); without the key it skips with a
reason naming the variable — never a failure, never a silent pass — which is why it
stays out of CI.

The pre-commit hook runs format check, lint, type check and unit tests;
commit messages must follow [Conventional Commits](https://www.conventionalcommits.org).
CI (GitHub Actions) runs those same gates on every push, plus three tiers the hook
leaves out: the integration tests, the React page's own, and the browser one.
