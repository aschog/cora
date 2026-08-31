## Context

Loading is `importlib.import_module` over a comma-separated list, and what a plugin
registered is visible only to the code that reads the registry.

## Goals / Non-Goals

**Goals** — two sources with one loader behind them, a source that travels with the
plugin, one listing read off the registrations already held, and a version on the
contract before an outside author binds us to it.

**Non-Goals** — entry-point discovery, deferred with a reason: a distribution
announcing itself serves an author who does not exist yet. A compatibility policy, which
waits for the first plugin it would bind. A registry of other people's plugins, which is
a website. Anything a plugin contributes to the screen beyond being listed on it.

## Decisions

**A source is a value on the extension, and finding is one function per source.**

- `Extension` gains the source it was found through, and every refusal quotes that
  rather than a module path.
- Two finders — the named modules, the folder's files — each yielding extensions, and
  the loader concatenates them.
- A third source is a third finder and an entry in the list, not a branch in the loader.
- The name-collision and version checks run over the concatenated list, so a dropped
  file collides with a named module exactly as two modules do.

**A folder file is imported by location, under the name of the file.**

- The file's stem is its name: it heads its section of the brief and names its settings,
  as a module's last segment does.
- Imported from its path rather than put on `sys.path`, so dropping a file in cannot
  shadow an installed module.
- Files only, sorted by name and loaded after the named modules: load order is
  precedence, and a deterministic one is what a deployment can reason about.
- Where the folder is, is a setting with a default beside cora's other stores.

**The contract version is a module attribute, read before `extend` is called.**

- Read where `extend` is looked up, because refusing after the plugin's code has run is
  not refusing.
- Absent means the version cora offers: today's plugins declare nothing and keep loading.
- The version cora offers is a constant in the port, beside the event names — it is
  contract, and a plugin reads it to know what it may write.
- Rejected: a call inside `extend`, which can only refuse a plugin that already ran.

**The listing is a projection of the registry, not a second record.**

- One method over the registrations already held, grouped by the module that made them.
- What is listed is what a turn would take, so a listing cannot drift from the app.
- The extensions supply the source, which no registration carries: the listing is the
  one place the two are joined.
- The scope field is what marks a registration system-wide, so the flag is read off the
  same value the filter is.
- A plugin that registered nothing is listed with nothing under it, because it is the
  one an operator most needs to see.

**One listing, two renderings, and neither builds it.**

- The terminal rendering is a module under `cora.app`, run over the app the deployment
  configured — so what prints is what loaded, not what a reader of the manifests guesses.
- The page's rendering is the same projection over HTTP, and the header menu draws it.
- Trade-off: the command assembles the app, so it wants the environment `make run`
  wants. Accepted — a listing that does not load the plugins is a listing of a guess.

**The guard widens from plugin names to scope names.**

- The existing guard reads every shipped file for a plugin's name; a scope is the same
  claim by another word.
- The names it forbids are the scopes the shipped plugins register under, read from the
  plugins rather than written into the guard.
- The component map is drawn from `assemble`'s signature, so a new source or a listing
  redraws it and its guard is what says so.
- No port is added: `Host` is unchanged, and `Extension` gains a field rather than a
  method.

## Risks / Trade-offs

- **A dropped file is arbitrary code with no manifest between it and the machine** →
  true of a named module too, and story 12 is where it is said rather than implied.
- **A version cora offers, with one version in existence, is a field nobody reads** →
  it is cheap now and impossible later: an author who already shipped cannot be asked
  to add one.
- **The listing names every tool a plugin registered** → it is the deployment's own
  configuration, and a listing that hid half of it would be worth less than none.
- **`make plugins` needs a key to print a listing** → it assembles what `make run`
  assembles, and the alternative is a listing that is not the one running.

## Migration Plan

None: `CORA_PLUGINS` keeps working unchanged, and a plugin declaring no version loads.
