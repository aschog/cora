# The packages

Which distribution to install, by what you are writing. Why the split falls here is
on [the big picture](../big-picture.md#the-distributions).

| If you are writing | You install | You do not get |
|---|---|---|
| a plugin, domain or guard | `cora` | it uses four names from `cora.ports` and `cora.domain`; the rest comes along |
| the app with a domain and a screen | `cora-plugin-fitness` · `cora-plugin-security` | nothing is loaded until `CORA_PLUGINS` names it |
| a third frontend | `cora` | Streamlit, Starlette, or any other way of talking to a user |
| the app you can run today | `cora-frontend-streamlit` | the plugins — it depends on `cora` and Streamlit, so a domain and a guard are installed and named separately |
| the same app in a browser page | `cora-frontend-react` | the widgets — it serves the engine over HTTP and a React build draws it |
