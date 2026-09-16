# Load plugins

A plugin does not have to be installed: drop it in the folder and cora loads it.
Writing one is [write a plugin](write-a-plugin.md); running cora at all is
[get started](get-started.md).

- Drop a `.py` file, or a folder holding `__init__.py`, into `./.cora/plugins/`. It is
  one plugin, named for the file or the folder, with no packaging at all — and a folder
  is imported as a package whose path is that folder, so a multi-file plugin's own
  relative imports resolve as written.
- The folder is read in name order, relative to where cora was started.
  `CORA_PLUGINS_PATH` moves it; `CORA_DEBUG` logs which folder it read.
- Nothing is installed for a drop-in: anything past cora and the standard library has
  to be in cora's environment already, or the plugin is refused by name.
- The folder is live. Dropped, deleted or edited, the next request has it — and the
  field it registers arrives and leaves with it. No restart.
- A symlink counts as its target, which is how this repo's own plugins deploy —
  [the four of them](get-started.md#load-the-plugins). Deleting a plugin from the page
  unlinks it rather than following it, so what it pointed at is untouched:
  [what cora does](../what-it-does.md#deleting-what-it-holds).

- Two plugins of one name are refused, and cora says which two — a name is what its
  settings and its section of the brief are keyed by, so one name is one plugin.
- A drop that cannot load refuses every request, readably and naming the plugin, until
  the folder loads again. The prior set serves on, and a turn already running finishes
  on the plugins it started with.
- `make plugins` prints what loaded — every plugin under where it came from, its tools,
  its instructions, the points in a turn it subscribed to, `system-wide` where it
  registered without a scope, and *has an effect* against a tool that acts outside cora.
  `GET /api/plugins` carries the same listing.
- A plugin declares which version of the contract it wants, and one cora does not offer
  is refused before its `extend` is called.

`CORA_PLUGIN_TRAVEL_SERPAPI_KEY` reaches `cora.plugins.travel` as `serpapi_key`: a
plugin's settings are named for it, and cora's own `CORA_` variables are a namespace no
plugin can read.
