# Story 13: One package, and only what I asked it to run

**As a** deployer · **I want** cora to install as one package and run only the plugins I
name · **So that** what is screening, answering and searching is what I asked for, and I
can see when nothing is

> **Given** cora installed with no plugin named
> **When** I start it and ask a question about my documents
> **Then** it starts and answers, and it says out loud that nothing screens what I type —
> and a plugin that carries no rule does not change that

Story 11 left the prompt-injection guard in a default set, so "no plugin" and "the guard"
were the same start. They are separated here: cora ships with no default, and says so.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(e2e)** browser.

#### One package, not five distributions

- [x] every shipped module falls under a layer rule, so a layer cannot arrive unguarded
- [x] every module a layer rule names is reached by the walk, so no rule passes vacuously
- [x] a `cora` layer imports nothing outside what its rule allows — read off the imports,
      not off a manifest, now that one distribution declares them all
- [x] a technology no manifest declares (`openai`, `torch`, `numpy`) is still out of reach
- [x] the walkers catch a planted violation, and pass innocent code
- [x] every wheel carries every module its package holds **(int)**
- [x] nothing on the path is named for a shipped namespace
- [x] the app carries no plugin and names none
- [x] a plugin needs the app and nothing else; a frontend needs the app and its toolkit
- [x] the app resolves without any user interface, and a plugin resolves it and stops **(int)**

#### Retrieval reads the index ingestion writes

- [x] `plain` searches the knowledge base the documents were written to
- [x] `advanced` plans queries and fuses what that same index returns
- [x] a mode no builder answers to is refused by name, not by `KeyError`
- [x] the allowed modes are exactly the registered builders, so config and dispatch
      cannot drift

#### A plugin is an extension cora starts without

- [x] cora assembles and answers with no plugin loaded
- [x] `CORA_PLUGINS` unset means no plugin, not a default set
- [x] bare cora warns that no plugin screens what the user types
- [x] a plugin that contributes no rule leaves that warning standing
- [x] a plugin that contributes a rule silences it
- [x] the modules that were loaded are named at `INFO`, by the path the user typed

#### The model may be named the way the key and the URL are

- [x] `OPENROUTER_MODEL` names the model when `CORA_MODEL` does not
- [x] `CORA_MODEL` wins when both are set
- [x] a name that is only blanks is no name at all — the alias still counts
- [x] a name is taken without the spaces around it

#### The docs still describe the tree

- [x] a config is read for the paths its comments write in backticks, and a path is
      claimed from its start rather than from a segment inside it
- [x] every location the docs claim exists
