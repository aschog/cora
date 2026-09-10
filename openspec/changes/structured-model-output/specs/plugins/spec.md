As a plugin author,\
I want the loop I delegate to answer in a shape I declared,\
so that a shape it could not produce fails loudly instead of reading as no result.

## MODIFIED Requirements

### Requirement: A registered tool may run a turn of its own

A tool SHALL be able to run its own bounded loop with the model, offered cora's document
search and the tools the plugin passed it. The system SHALL offer such a loop none of its
own tools that write or stop a turn, and SHALL bound what one loop and everything it
delegates may spend. A loop that reaches that bound SHALL report what it found, saying it
stopped early, rather than losing it or presenting it as complete. A loop that gathered
nothing SHALL refuse instead, so no write-up is asked of an empty transcript. The system SHALL report
the steps of that loop as children of the call that ran it, and SHALL require no change of
its own to allow it.

A tool SHALL be able to declare the shape it needs the loop to answer in, and what comes
back SHALL be a value that satisfies it. The system SHALL hold the provider to that shape
rather than asking for it in words. Where an answer satisfying it cannot be had — the
model will not be held to a shape, or what arrived does not satisfy one — the system SHALL
refuse the call and say which of the two happened, and SHALL never hand back a value it
read loosely. A tool that declares no shape SHALL read what the loop wrote, unchanged.

#### Scenario: A tool runs its own bounded loop

- **GIVEN** a plugin registering a tool that runs a model loop of its own
- **WHEN** the model calls that tool
- **THEN** the tool runs, and the turn is answered
- **AND** the loop is offered no tool of cora's that writes or stops the turn

#### Scenario: A loop spends what the host allows and no more

- **GIVEN** a loop asking for more rounds than the host allows, at any depth
- **WHEN** it runs
- **THEN** it is stopped at the host's allowance, and the turn's own is untouched

#### Scenario: A loop stopped at its ceiling reports what it has

- **GIVEN** a loop that spends its allowance without reaching an answer
- **WHEN** it stops
- **THEN** it reports what it found so far, and says it stopped early
- **AND** what it gathered is not discarded, and is not offered as a complete answer

#### Scenario: A loop that gathered nothing refuses rather than reporting

- **GIVEN** a loop stopped with nothing looked up in it
- **WHEN** it stops
- **THEN** it refuses, no write-up is asked for, and nothing is presented as a finding

#### Scenario: A spent allowance is not a model call per nested lookup

- **GIVEN** a loop whose allowance is gone, and a round that fans out many ways
- **WHEN** each nested lookup runs
- **THEN** none of them spends a model call of its own, however wide the fan-out

#### Scenario: The loop's steps are shown under the call

- **WHEN** the trace of that turn is read
- **THEN** the loop's steps are children of the call, in the order they were taken

#### Scenario: What a loop read is named rather than numbered

- **GIVEN** a loop that searched the user's documents
- **WHEN** it answers
- **THEN** it was shown each passage under its document's name, as the document was
  written
- **AND** what it answered carries no citation number of its own

#### Scenario: A declared shape comes back as a value, not as prose

- **GIVEN** a tool delegating a loop and declaring the shape it needs
- **WHEN** the loop answers
- **THEN** the tool is handed a value satisfying that shape, with nothing left to parse

#### Scenario: A model that will not be held to a shape refuses the call

- **GIVEN** a deployment whose model cannot be held to a declared shape
- **WHEN** a tool delegates a loop declaring one
- **THEN** the call refuses, the refusal names the model, and no answer is read loosely

#### Scenario: An answer that does not satisfy the shape refuses too

- **GIVEN** a loop whose answer arrives cut short or otherwise unsatisfying the shape
- **WHEN** the tool reads it
- **THEN** the call refuses, saying the shape was not satisfied, and nothing is guessed at

#### Scenario: A loop asked for no shape is unchanged

- **GIVEN** a tool delegating a loop and declaring no shape
- **WHEN** the loop answers
- **THEN** the tool reads the prose the loop wrote, as it did before
