As someone writing a plugin,\
I want cora to hand me what it has and let me register what I have,\
so that what I can contribute is not limited to the fields someone else thought of.

## ADDED Requirements

### Requirement: A plugin registers what it has

The system SHALL load a plugin by calling `extend` on its module, and SHALL offer
whatever that call registered: its tools callable, its instructions in the brief, its
rules screening what the user types. The system SHALL accept no other way of
contributing.

#### Scenario: A plugin registers rather than declares

- **GIVEN** a module defining `extend(cora)` and no record of contributions
- **WHEN** it is loaded
- **THEN** its tools are callable, its instructions are in the brief, and its rules screen
  the input

#### Scenario: The plugins cora ships carry no record

- **GIVEN** the security and fitness plugins as they are shipped
- **WHEN** their modules are read
- **THEN** each registers through `extend`, and neither leaves a record behind

### Requirement: A plugin is handed cora's own parts

The host SHALL give a plugin what cora has: document search, what cora remembers, and
the model itself. It SHALL also give the plugin a log and settings of its own, both
named for the plugin rather than for cora.

#### Scenario: A plugin uses cora's own parts

- **GIVEN** a plugin that wants to search, to remember, or to call the model
- **WHEN** it is loaded
- **THEN** the host it was handed offers each of those

#### Scenario: What a plugin logs and reads is named for it

- **GIVEN** a loaded plugin that writes a log line and reads a setting
- **WHEN** the line is written and the setting is read
- **THEN** both are named for that plugin

### Requirement: A registered tool may run a turn of its own

A tool SHALL be able to run its own bounded loop with the model, offered cora's document
search and the tools the plugin passed it. The system SHALL offer such a loop none of its
own tools that write or stop a turn, and SHALL bound what one loop and everything it
delegates may spend. The system SHALL report the steps of that loop as children of the
call that ran it, and SHALL require no change of its own to allow it.

#### Scenario: A tool runs its own bounded loop

- **GIVEN** a plugin registering a tool that runs a model loop of its own
- **WHEN** the model calls that tool
- **THEN** the tool runs, and the turn is answered
- **AND** the loop is offered no tool of cora's that writes or stops the turn

#### Scenario: A loop spends what the host allows and no more

- **GIVEN** a loop asking for more rounds than the host allows, at any depth
- **WHEN** it runs
- **THEN** it is stopped at the host's allowance, and the turn's own is untouched

#### Scenario: The loop's steps are shown under the call

- **WHEN** the trace of that turn is read
- **THEN** the loop's steps are children of the call, in the order they were taken

#### Scenario: What a loop read is named rather than numbered

- **GIVEN** a loop that searched the user's documents
- **WHEN** it answers
- **THEN** it was shown each passage under its document's name, as the document was
  written
- **AND** what it answered carries no citation number of its own

### Requirement: A plugin cora cannot have is refused by name

The system SHALL refuse a plugin it cannot load, and the refusal SHALL name the module
and what is wrong with it. A module defining no `extend`, one that raises while
registering, one registering a name cora has already taken, and two modules whose names
end alike are each refused.

#### Scenario: A module that does not register is refused

- **GIVEN** a module defining no `extend`
- **WHEN** cora starts
- **THEN** it refuses, naming that module and saying it registers nothing

#### Scenario: A module that fails while registering is refused

- **GIVEN** a module whose `extend` raises
- **WHEN** cora starts
- **THEN** it refuses, naming that module and what went wrong inside it

#### Scenario: A name cora has already taken is refused

- **GIVEN** a module registering a tool under a name cora offers itself
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the name it may not take

#### Scenario: Two plugins that cannot be told apart are refused

- **GIVEN** two modules whose paths end in the same name
- **WHEN** cora starts
- **THEN** it refuses, naming both and the name they share

### Requirement: What a plugin read for cora is labelled untrusted

The system SHALL label as untrusted whatever reaches a model out of the user's documents.
This SHALL hold for the passages a plugin's own loop read, for what that loop answered
after reading them, and for a plugin that searched the documents itself.

#### Scenario: A delegated loop reads its passages behind the label

- **GIVEN** a loop that searched the user's documents
- **WHEN** it is shown what the search found
- **THEN** the passages arrive labelled untrusted, as a turn's own search labels them

#### Scenario: What a loop answered reaches the turn labelled

- **GIVEN** a tool whose loop read the documents and answered in its own words
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted, though it carries no passage

#### Scenario: A plugin that searches for itself says so

- **GIVEN** a plugin whose tool searches the documents without delegating
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted
