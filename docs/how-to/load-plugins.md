# Load plugins

Two routes, and neither is a fork: name the module in `CORA_PLUGINS`, or drop the plugin
into the folder. Writing one is [write a plugin](write-a-plugin.md); running cora at all
is [get started](get-started.md).

- Drop a `.py` file, or a folder holding `__init__.py`, into `./.cora/plugins/`. It is
  one plugin, named for the file or the folder, with no packaging at all.
- The folder is read in name order after the modules `CORA_PLUGINS` names, relative to
  where cora was started. `CORA_PLUGINS_PATH` moves it; `CORA_DEBUG` logs which folder
  it read.
- Nothing is installed for a drop-in: anything past cora and the standard library has
  to be in cora's environment already, or the plugin is refused by name.
- The folder is live. Dropped, deleted or edited, the next request has it — and the
  field it registers arrives and leaves with it. No restart.
- A symlink counts as its target, so this repo's own plugins deploy by linking:

  ```sh
  ln -s "$(pwd)"/plugins/travel/src/cora/plugins/travel .cora/plugins/travel
  ```

- One route per plugin: a module `CORA_PLUGINS` names *and* a link in the folder are two
  plugins with one name, which cora refuses. Only the folder is live; what
  `CORA_PLUGINS` names is fixed at start.
- A drop that cannot load refuses every request, readably and naming the plugin, until
  the folder loads again. The prior set serves on, and a turn already running finishes
  on the plugins it started with.
- `make plugins` prints what loaded — every plugin under where it came from, its tools,
  its instructions, the points in a turn it subscribed to, and `system-wide` where it
  registered without a scope. `GET /api/plugins` carries the same listing.
- A plugin declares which version of the contract it wants, and one cora does not offer
  is refused before its `extend` is called.

`CORA_PLUGIN_TRAVEL_SERPAPI_KEY` reaches `cora.plugins.travel` as `serpapi_key`: a
plugin's settings are named for it, and cora's own `CORA_` variables are a namespace no
plugin can read.
