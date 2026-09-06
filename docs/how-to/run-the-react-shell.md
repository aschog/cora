# Run the React shell

`make run` builds the page and serves it with the API from one process on
`127.0.0.1:8000`. That is cora — there is no second screen to choose between.

`make run-env` is the same command reading its environment from `.env` instead of from
the shell you typed in, which is how the live test tier is run too. Put `CORA_PLUGINS`
there as well, or cora starts with none.

Both need Node 22 and the page's dependencies — `npm ci --prefix frontends/react/ui`,
once per clone. Neither the dependencies nor the build is committed, so without that
first step it is the build that fails rather than the server.

## Working on the page

The server reads only the build at `frontends/react/ui/dist`, so a source change is
invisible until something rebuilds it. `make run` does that first, which is enough for
running cora but not for writing the page: rebuilding on every keystroke is not a loop.

Run `make run` and `make ui` side by side instead. Vite serves the page on `5173` and
proxies `/api` to the first, so a saved file is on the screen immediately. `make ui-build`
is the same build on its own, for when you want the served page current without the dev
server.

A setting the shell cannot use is refused before anything is built, as one line on
stderr and a non-zero exit.

## The page's own gates

Four, and CI runs all of them; the commit hook runs none, because they need Node and a
commit that touches no TypeScript should not wait for it:

```sh
npm --prefix frontends/react/ui run lint          # eslint, and the hook rules with it
npx --prefix frontends/react/ui tsc -b            # type check
npm --prefix frontends/react/ui test              # unit tier, happy-dom
npm --prefix frontends/react/ui run test:browser  # the tier that needs a real cascade
```

`lint` is the one no type checker can stand in for: the order hooks are called in, and a
dependency array that has fallen behind the closure it belongs to.

Styles are per component — `Answer.module.css` beside `Answer.tsx` — so a class reaches
what the file it sits beside draws and nothing else. `src/styles.css` keeps what is
genuinely everyone's: the colour and spacing tokens, the resets, and the few utilities
several components share. A test that needs a class imports the module and reads the name
off it, because the name in the file is not the name in the DOM.

## The address bar

A conversation you open is named in the address, as `#/c/<thread>`. That makes it a link
you can send, a page you can reload back into, and something the back button walks. The
hash rather than the path because the built page is served as static files with no
fallback: `/c/<thread>` would ask the server for a file it does not have.

Starting a new conversation takes it back out — a fresh thread is in no store and there is
nothing to link to yet.

A card left open still outranks the address on a reload. A conversation named there is
listed under SESSIONS and is one click away; a thread parked on its first question has
answered nothing, is listed nowhere, and is reachable by the stow and by nothing else.
