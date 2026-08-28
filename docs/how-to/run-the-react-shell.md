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
