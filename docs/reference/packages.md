# The packages

Which distribution to install, by what you are writing. The boundary the split falls on
is drawn on [the map](../big-picture.md#the-map).

| If you are writing | You install | You do not get |
|---|---|---|
| a plugin, domain or guard | `cora` | it uses four names from `cora.ports` and `cora.domain`; the rest comes along |
| the app with a domain and a screen | `cora-plugin-fitness` · `cora-plugin-security` | nothing is loaded until `CORA_PLUGINS` names it |
| a third frontend | `cora` | Streamlit, Starlette, or any other way of talking to a user |
| the app you can run today | `cora-frontend-streamlit` | the plugins — it depends on `cora` and Streamlit, so a domain and a guard are installed and named separately |
| the same app in a browser page | `cora-frontend-react` | the widgets — it serves the engine over HTTP and a React build draws it |

## What each package ships

| Package | Ships | Depends on |
|---|---|---|
| `cora` | `cora.domain` · `cora.ports` — the contract<br>`cora.engine` — the agent, the knowledge base, a turn's steps<br>`cora.adapters` — Chroma, OpenRouter, LangGraph, MiniLM<br>`cora.app` — the composition root and its configuration | its technologies, and no user interface |
| `cora-plugin-security` | `cora.plugins.security` — the prompt-injection screen | `cora` |
| `cora-plugin-fitness` | `cora.plugins.fitness` — the reference domain plugin | `cora` |
| `cora-frontend-streamlit` | `cora.frontends.streamlit` — the app as a Streamlit page | `cora` |
| `cora-frontend-react` | `cora.frontends.react` — the same app over HTTP, drawn by a React page | `cora` |

## Where each one lives

The tree says which is which by its position:

```
src/cora/                          domain  ports  engine  adapters  app
plugins/fitness  plugins/security  one of many — the directory expects siblings
frontends/streamlit  frontends/react
```

`src/` is the app; a directory beside it is an extension point, named in the plural for
that reason. So `ls` is the shortest description of what can be extended.
