# Story 11: The plugins I choose, or none

**As a** cora user · **I want** to load the plugins I choose, or none at all · **So that** the
agent carries exactly the domains and guards I asked for, and nothing I didn't

> **Given** `CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness`
> **When** I ask a training question, then ask for a diagnosis, then try to override cora's
> instructions
> **Then** the first is answered from my documents with a citation, the second is refused by
> the fitness medical rule and the third by the security plugin's injection screen — one app,
> both plugins live at once

> **Given** `CORA_PLUGINS=` set empty
> **When** I ask the same training question
> **Then** the same cora answers as a plain assistant: no persona, no refusals, no grounding
> gate, and no second model call

This inverts what cora *is*. Today fitness **is** cora unless an env var says otherwise —
`DEFAULT_PLUGIN` is the fitness module and `load_plugin` binds exactly one. After this story
cora is domain-agnostic on its own, and every persona, restriction and specialisation
arrives as a plugin. The default set ships one, `cora.plugins.security`, so the box is safe
without being opinionated.

## The shape

```
Plugin        name · instructions · tools · validation_rules · scope — data, in ports
PluginSet     the ordered set, composed: preamble + sections, cora's tools then theirs,
              every rule, one reminder over every scope — engine, beside the registry
cora-security cora.plugins.security — PromptInjectionRule, out of the engine
```

- **Everything but `name` is optional.** The loader rejects a bundle with no tools today
  (`plugin_registry.py:36`), which makes a rules-only security plugin illegal. A plugin
  contributes whatever it has, and the dataclass becomes `kw_only`: with one required field
  and four defaults, declaration order would otherwise be API, and a fifth contribution kind
  has to be an appended field rather than a break.
- **`system_prompt` becomes `instructions`, `grounding` becomes `scope`.** Both were the
  whole thing and are now a part of it: cora writes the preamble and words the reminder, the
  plugin supplies its section and the phrase naming what its documents cover. N phrases join;
  N paragraphs contradict each other.
- **`seed_docs` is dropped.** `build()` already passes `seed=False` (`assembly.py:210`, commit
  4923d59), so nothing in the shipped app ingests them. Documents are the user's and arrive by
  upload — and with one store and no per-plugin filter, seeded passages outlive the plugin
  that added them.
- **Config order is composition order** — sections, tool offers and rule precedence all read
  down the list. It is the only ordering rule.
- **Collisions are config errors, and the set is what raises them.** The reserved-name check
  lives in the composition root today (`assembly.py:137-158`) while every other plugin
  refusal lives in `plugin_registry.py`; this story adds a second collision, so both move
  onto `PluginSet` and `assemble` reads composed fields and rejects nothing. A third
  collision is then a check on one object, not another branch in the root. Errors quote
  module paths, which are what the user typed; `name` only words a prompt heading, so two
  plugins may share one. Paths are *not* unique by construction, though —
  `CORA_PLUGINS=a,a` would otherwise read as "a and a both offer `calculate_bmi`", so a
  path listed twice is its own refusal, ahead of the tool check. Not deduped silently: it
  is a typo in something the user wrote.
- **Two error types survive, and that is the seam, not sloppiness.** A module that won't load
  raises `PluginLoadError`, a set that won't compose `ConfigurationError`. The UI treats them
  alike (`chat.py:31`, `except CoreError`); the split says whether the plugin or the
  combination is what the user has to change.
- **Cora's own rules move into the engine, beside the set.** `EmptyInputRule`, `MaxLengthRule`
  and `MAX_INPUT_CHARS` are built in the composition root today
  (`assembly.py:53,104-111`). If `PluginSet` is what puts cora's rules ahead of every
  plugin's, it has to hold them — otherwise the order is still the root's doing and the test
  for it sits in the wrong package. `MAX_FACT_CHARS` already sits beside the tool it sizes
  (`memory_tool.py:9`).
- **Validation happens once**, in `PrepareStep`, immediately before the model step. Two
  seams go with the change:
  - `ValidationPipeline` and `InputValidator` **go entirely** (`validation.py:9-14,65-73`).
    `core_rules`/`plugin_rules` stops naming a distinction once the injection rule is a
    plugin rule and `_fact_rules()` — the only *production* caller that ever passed
    `plugin_rules=()` — is gone. What is left then is a Protocol with one implementation, one
    consumer (`steps.py:60`) and a body that loops over a tuple and hands back its argument,
    so `PrepareStep` takes the tuple and does the loop. `PluginSet` composes that tuple
    anyway; a class whose only job is to hold it is a hop, not a seam. `ValidationRule`
    stays — that one is the plugin author's port. Three tests pass the empty second tuple;
    `test_langgraph_runner.py:235` is the one outside the engine and app suites, and the easy
    miss on the sweep.
  - `_fact_rules()` goes: the `remember` tool keeps a non-blank check and a length cap as
    plain guards, which stop a blank or oversized blob reaching the store and are not prompt
    validation. With one answer left, `RememberFact.validation`, its `None` branch and
    `_checked` (`memory_tool.py:28,40-46`) go too — the seam existed only because assembly
    had a second pipeline to pass. The `refusal` argument on cora's three rules
    (`validation.py:35-38,48,58`) loses its last caller with it — only the fact path ever
    overrode those messages — and it is cheaper to take off now than after the injection rule
    emigrates to `cora-security`. The returned-input hop goes the same way: nothing rewrites
    input, so `PrepareStep` reads `state["question"]`.

  A stored fact is therefore no longer screened for injection — the engine cannot import a
  rule that now lives in a plugin — and it is replayed into the brief every turn
  (`steps.py:221`). `REMEMBERED_NOTICE` is what stands behind it, and already ships.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.
**(moved)** marks a test that relocates rather than a new one.

#### First, the outer test

- [x] **(int)** security and fitness loaded together: a training question is answered with a
      citation, a diagnosis question is refused by the medical rule, and an override attempt
      is refused by the injection screen — the marker was dropped and it passed

It passes with the substring matcher `sprint-4-feedback.md` has open as broken, which
refuses "I have diabetes, how should I train?" outright. The rule is here to show a domain
plugin refusing beside a guard plugin; this story does not fix it, and the backlog item has
had no story since story 6 left the cut.

#### A plugin contributes what it has

- [x] a bundle carrying only `name` and `validation_rules` loads — today's loader refuses it
      for having no tools, which is what makes a security plugin impossible
- [x] a bundle carrying only `name` and `tools` loads and contributes no prompt section
- [x] a blank `name` is a `PluginLoadError`
- [x] no module in the workspace reads `seed_docs`, and `assemble` has no `seed` flag
      *(moved — the seeding tests go with the field)*

#### Zero plugins is a working app

- [x] `CORA_PLUGINS` set empty assembles an app with no plugin instructions, no plugin rules
      and no gate; unset resolves to `cora.plugins.security` alone — the two must stay
      distinguishable or bare cora cannot be asked for
- [x] bare cora's system prompt is the preamble alone and names no domain
- [x] bare cora answers without a refusal and without a second model call, no scope having
      been declared
- [x] the `remember` tool stores a fact with no validation behind it, and still refuses a
      blank one and one over the length cap — `remember_tool` takes a memory and nothing else

#### The set composes in order

- [x] two plugins' instructions appear as two sections under their names, in config order,
      between cora's preamble and the remembered facts — cora's rules first, then the
      domains, then the user's own notes. That is a flip: today the plugin prompt comes
      first and the rules after it (`steps.py:87,94`), and `test_steps.py:403` asserts
      membership, not order, so nothing currently catches it
- [x] the offered tools are cora's first, then each plugin's in list order
- [x] every plugin's rules run, and the first refusal in list order is the message the user
      sees — cora's own rules ahead of all of them
- [x] no module imports `ValidationPipeline` or `InputValidator` — `PrepareStep` holds the
      tuple *(the pipeline's three tests in `test_validation.py:104-138` are deleted, not
      rewritten: the two items above are the same assertions where the order is now decided)*
- [x] two scopes join into one reminder; a plugin with an empty scope adds nothing to it, and
      one plugin with a scope is enough to turn the gate on

#### Collisions are config errors, not surprises

- [x] two plugins offering the same tool name is a `ConfigurationError` naming both module
      paths and the tool
- [x] the same module path listed twice is its own `ConfigurationError`, ahead of the tool
      check — otherwise the collision error names a plugin as colliding with itself
- [x] a plugin taking `search` or `remember` raises today's error, now naming the module
      *(moved — off `assemble`, onto the set)*
- [x] one unimportable module in a list of three names that module, not the list
- [x] both collisions are raised by `PluginSet`, not by `assemble`: the composition root
      wires an already-valid set, so `ConfigurationError` is no longer named in `assembly.py`

#### Security becomes a plugin

- [x] **(int)** `cora-security` builds as a wheel and imports in a clean venv with
      `cora.engine` absent — the seventh distribution, on story 10's terms
- [x] the architecture guards walk *both* plugin distributions: `test_architecture.py:44`
      reaches the layer as `_root(cora.plugins.fitness).parent`, so a second plugin tree is
      one the streamlit-containment and no-test-framework guards never open — they pass by
      finding nothing. Roots come from the workspace glob, as `test_docs.py` and
      `test_packaging.py` already do, and a mutation shows the wider walk bites
- [x] `PromptInjectionRule` is absent from `cora.engine.validation`, and the security plugin
      carries it *(moved)*
- [x] the default set refuses an override attempt in the conversation, and bare cora does
      not — the guard is opt-out by design

#### Nothing else changed

- [x] **(int)** the app assembles and answers a document question through the composition
      root, exactly as before
- [x] **(llm)** the live acceptance answers a training question with a citation, fitness now
      named explicitly *(moved)*
- [x] `README.md` and `big-picture.md` name `CORA_PLUGINS`, the default set, the seven
      distributions, and that bare cora screens nothing; `spec.md`'s bonus bar stops
      claiming the injection screen as `engine/validation.py` and says where it went

## Order

1. the contract opens up — optional fields, `kw_only`, `name` in, `seed_docs` out; still one
   plugin
2. `PluginSet` and `load_plugins`; it takes over the collision checks — reserved name, tool
   clash, duplicate path — and cora's own rules with them, and `assemble` takes the set. It
   exposes the composed rules as a **tuple**, not a pipeline: that is what decides step 6, and
   it is cheap to choose here and expensive to reverse there. `assemble`'s `loaders` parameter
   goes while the signature is open — no caller has ever passed it, and a test wanting other
   loaders builds `KnowledgeBase` directly
3. `CORA_PLUGINS` becomes a list
4. cora takes the preamble and words the reminder; `instructions` and `scope` are renamed and
   the fitness plugin is rewritten to a section and a phrase. `PrepareStep._brief()` is
   rewritten here anyway, so its `memory is None` early return goes with it: one section
   list with conditional members, not two joins (`steps.py:87,95`)
5. `PromptInjectionRule` leaves for `cora-security`, and the default set changes; the
   architecture guards widen to the workspace before the second plugin tree exists to hide in
6. `_fact_rules()` goes, and behind it `ValidationPipeline`, `InputValidator` and the `refusal`
   argument — every last caller of the three is in what this step deletes, and `PrepareStep`
   takes the tuple step 2 hands it
7. docs and diagram

Steps 1 and 4 are each one atomic commit: a renamed field with the old text still in the
plugin is a prompt that says everything twice.

## Out of scope

- **Stronger injection rules** (LLM Guard or similar), the open backlog item. This story is
  what unblocks it — it does not write it.
- **A UI picker.** Composition happens at assembly from the environment, which is what keeps
  the developer settings out of the user experience.
- **A second domain plugin.** The composition is proven by a guard beside a domain, not by a
  new domain.
- **Saying so when the store is empty.** An in-scope question with nothing indexed is still
  answered from model knowledge, uncited. [Story 12](../story-12.md) changes that, and needs the
  reminder step 4 moves into cora before it can.
- **Retrieval settings, UI panels and specialist sub-agents as contributions.** Four
  contribution kinds; a fifth is a field with a default later, not a breaking change.
- **Entry-point discovery.** Still the later convenience story 10 called it.
