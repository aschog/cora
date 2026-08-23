# Run the React shell

The same app behind an HTTP surface, with a React page instead of Streamlit.

`make run-react` builds the page and then serves it with the API from one process on
`127.0.0.1:8000`; in development run `make run-react` and `make ui` side by side, and
Vite serves the page on `5173`, proxying `/api` to the first. The server reads only the build at `frontends/react/ui/dist`, so
`make ui` is the one that shows a source change as you save it — `make ui-build` is the
same build on its own.

A setting the shell cannot use is refused before anything is built, as one line on
stderr and a non-zero exit.
