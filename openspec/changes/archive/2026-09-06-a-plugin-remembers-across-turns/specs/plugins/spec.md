As a plugin author,\
I want to keep what my plugin worked out between the turns of one conversation,\
so that the next turn builds on it rather than starting again.

## Purpose

What a plugin may keep, where it is kept, and when it goes. A plugin that works
something out over several turns holds it here, rather than hoping the transcript still
carries it.

## ADDED Requirements

### Requirement: A plugin keeps what it worked out, for the length of a conversation

A plugin SHALL be able to keep text under a name of its choosing, and read it back on a
later turn of the same conversation. A name nothing was kept under SHALL read as
nothing, rather than as a failure.

#### Scenario: What one turn kept, the next turn reads

- **GIVEN** a plugin whose tool keeps a value under a name
- **WHEN** a later turn of that conversation calls a tool that reads the name
- **THEN** the value it kept comes back

#### Scenario: Another conversation reads nothing

- **GIVEN** a plugin that kept a value in one conversation
- **WHEN** its tool reads that name in a second conversation
- **THEN** nothing comes back, and the first conversation still holds its value

#### Scenario: A name nothing was kept under

- **GIVEN** a plugin that has kept nothing
- **WHEN** its tool reads any name
- **THEN** nothing comes back and the turn answers

#### Scenario: Keeping nothing under a name drops it

- **GIVEN** a plugin that kept a value under a name
- **WHEN** its tool keeps nothing under that same name
- **THEN** a later read of it comes back with nothing

### Requirement: What a plugin keeps is its own

Names SHALL be held per plugin. One plugin SHALL NOT read or overwrite what another
kept, whichever name either chose.

#### Scenario: Two plugins use the same name

- **GIVEN** two plugins that each keep a different value under the name `plan`
- **WHEN** each reads `plan` in the same conversation
- **THEN** each reads back its own value

### Requirement: A plugin outside a turn keeps nothing

Reading or writing outside a tool call SHALL come back with nothing and record nothing,
because there is no conversation for it to belong to.

#### Scenario: A plugin writes while it is being loaded

- **GIVEN** a plugin that keeps a value inside its own `extend`
- **WHEN** a turn later reads that name
- **THEN** nothing comes back, and loading the plugin did not fail

### Requirement: What a plugin kept goes when the conversation goes

Deleting a conversation SHALL delete what its plugins kept in it, as it deletes the
turns and the thread they were answered on.

#### Scenario: A deleted conversation keeps nothing behind

- **GIVEN** a conversation in which a plugin kept a value
- **WHEN** that conversation is deleted
- **THEN** a new conversation on that thread reads nothing under the name

#### Scenario: Deleting one conversation leaves another alone

- **GIVEN** two conversations in which the same plugin kept different values
- **WHEN** one of them is deleted
- **THEN** the other still reads back its own value
