As a plugin author,\
I want a store of my own that outlives the conversation,\
so that what my plugin worked out is still there tomorrow.

## ADDED Requirements

### Requirement: A plugin is handed a store of its own

Cora SHALL hand a plugin a store it can read and write by name, holding text, which
outlives the turn, the conversation and the process. What a plugin keeps SHALL be
namespaced under the name cora loaded it as, so two plugins using one name keep two
values and neither reads the other's. Keeping nothing under a name SHALL drop it.

#### Scenario: What was kept is read back

- **GIVEN** a plugin that kept text under a name
- **WHEN** it reads that name in a later turn
- **THEN** the text it kept comes back

#### Scenario: Two plugins, one name

- **GIVEN** two plugins that kept different text under the same name
- **WHEN** each reads that name
- **THEN** each reads its own

#### Scenario: A name nothing was kept under

- **WHEN** a plugin reads a name it never kept anything under
- **THEN** it reads nothing, and nothing fails

#### Scenario: A name dropped

- **GIVEN** a plugin that kept text under a name
- **WHEN** it keeps nothing under that name
- **THEN** reading the name comes back with nothing

### Requirement: A deployment without a store hands none

Where the deployment keeps no file of its own, the store SHALL be absent rather than
silently empty, so a plugin that needs one can say so instead of losing what it keeps.

#### Scenario: No store to keep anything in

- **GIVEN** a deployment assembled with no store
- **WHEN** a plugin reads what it was handed
- **THEN** it is handed nothing, and it is the plugin's to say so

### Requirement: What a plugin keeps is not what cora knows

What a plugin keeps in its own store SHALL NOT appear in the brief, in what cora
recalls about the user, or in any rail that lists what cora knows.

#### Scenario: A plugin's store is not memory

- **GIVEN** a plugin that kept text in its own store
- **WHEN** what cora knows about the user is read
- **THEN** what the plugin kept is not among it
