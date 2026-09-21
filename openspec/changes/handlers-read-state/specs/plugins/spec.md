As a plugin author,\
I want my answer handler to read what my tools kept this turn,\
so that I can check the answer against what was actually put.

## ADDED Requirements

### Requirement: A plugin's answer handler reads what it kept

While a plugin's handler runs on the answer, it SHALL read what that plugin kept for the
conversation, and what it keeps there SHALL be kept, as inside one of its tool calls.
A handler of another plugin SHALL read nothing of it.

#### Scenario: A handler reads what a tool kept

- **GIVEN** a plugin whose tool kept a value under a name this turn
- **WHEN** its answer handler reads that name
- **THEN** the value comes back

#### Scenario: A handler keeps something

- **GIVEN** a plugin whose answer handler keeps a value under a name
- **WHEN** a later turn of that conversation calls one of its tools that reads the name
- **THEN** the value comes back

#### Scenario: Another plugin's handler

- **GIVEN** two plugins, one of which kept a value
- **WHEN** the other's answer handler reads that name
- **THEN** nothing comes back
