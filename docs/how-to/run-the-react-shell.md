# Run the React shell

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000` — install, plugins, the `.env` semantics and
[the gates](get-started.md#gates) are [get started](get-started.md). This page is what
only matters once you are working on the page itself.

The server reads the *built* page — `CORA_UI_PATH`, or `frontends/react/ui/dist` where
that is unset — and mounts nothing when it is absent, so a source change is invisible
until something rebuilds it. `make ui-build` is that build on its own.

## Working on the page

Run `make ui` beside `make run`: the dev server comes up on Vite's default
`127.0.0.1:5173` and proxies `/api` to `127.0.0.1:8000`, so a saved file is on the screen
without a rebuild. `127.0.0.1:8000` still shows the last build.

A setting cora cannot use is refused as one line on stderr and a non-zero exit rather
than a traceback — and under `make run` the page is built before that line appears,
because the target builds first.

## The style guard

`npm run lint`, inside `frontends/react/ui`, is two tools: eslint, and its own
`scripts/check-styles.mjs`.

- eslint runs the JS and TypeScript recommended sets, plus the React rules a type
  checker cannot state: the order hooks are called in, a dependency array that has
  fallen behind its closure, and `react-refresh/only-export-components` — which is what
  lets a save replace a component rather than reload the page and lose the conversation
  on it.
- `vite/client` types a CSS module as a string-indexed record, so `styles.narrow`
  type-checks whether or not `.narrow` is declared, and is `undefined` at runtime: the
  element is drawn with the word "undefined" for a class. `check-styles.mjs` is the only
  thing in the toolchain that looks.
- It also catches a rule left in the global sheet naming a class only a module now
  declares — the dead rule a split stylesheet leaves behind. It reads class literals off
  the components, so a class reached only through `joined()` or a ternary reads as
  undrawn: where a module also declares that name, the check fails naming a rule that is
  not dead. Loud at lint rather than silent in the page.

Styles are per component — `Answer.module.css` beside `Answer.tsx` — declared kebab-case
in the sheet and reachable only as the camelCase name from TypeScript, because
`camelCaseOnly` drops the kebab key. A module two components share is named for the
thing instead, like `dialog.module.css`. That leaves `src/styles.css` holding the
tokens, the resets, the keyframes and the handful of names more than one component draws
with.

A test that needs a class imports the module and reads the name off it, because the name
in the file is not the name in the DOM.

## The address bar

A conversation you open is named in the address as `#/c/<thread>`, which makes it
linkable, reloadable and walkable with the back button. Starting a new one takes the name
back out.

The hash rather than the path, because the built page is served as static files with no
fallback: `/c/<thread>` would ask the server for a file it does not have.

A card left open still outranks the address on a reload — what the page stowed comes
first, then the address, then a new conversation.
