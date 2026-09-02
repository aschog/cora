As a person asking something that takes several lookups,\
I want cora to delegate the digging and come back with one answer,\
so that a broad question is answered without the searching itself filling the
conversation.

## MODIFIED Requirements

### Requirement: A registered tool may run a turn of its own

A tool SHALL be able to run its own bounded loop with the model, offered cora's document
search and the tools the plugin passed it. The system SHALL offer such a loop none of its
own tools that write or stop a turn, and SHALL bound what one loop and everything it
delegates may spend. A loop that reaches that bound SHALL report what it found, saying it
stopped early, rather than losing it or presenting it as complete. The system SHALL report
the steps of that loop as children of the call that ran it, and SHALL require no change of
its own to allow it.

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

#### Scenario: A loop that found nothing says that instead

- **GIVEN** a loop stopped at its ceiling having found nothing to report
- **WHEN** it stops
- **THEN** it says so, and nothing is presented as a finding

#### Scenario: The loop's steps are shown under the call

- **WHEN** the trace of that turn is read
- **THEN** the loop's steps are children of the call, in the order they were taken

#### Scenario: What a loop read is named rather than numbered

- **GIVEN** a loop that searched the user's documents
- **WHEN** it answers
- **THEN** it was shown each passage under its document's name, as the document was
  written
- **AND** what it answered carries no citation number of its own

## ADDED Requirements

### Requirement: A tool says whether it changes anything outside cora

A plugin registering a tool SHALL be able to declare that calling it changes something
outside cora. The declaration SHALL belong to the tool, and a tool declaring nothing SHALL
be taken as changing nothing.

#### Scenario: A tool is registered as having an effect

- **GIVEN** a plugin registering a tool that declares one
- **WHEN** the plugins are listed
- **THEN** that tool is shown as having an effect, and its neighbours are not

#### Scenario: A tool declaring nothing is read as changing nothing

- **GIVEN** a tool registered without the declaration
- **WHEN** a turn offers it
- **THEN** it is treated as reading only

### Requirement: A sub-agent reads and does not act

The system SHALL offer a delegated loop no tool that declares an effect, and no tool of
its own that writes or stops a turn. A loop SHALL therefore be unable to propose an effect
or to stop and ask, whatever the plugin that ran it passed in.

#### Scenario: An effect is withheld from a delegated loop

- **GIVEN** a scope holding both a researcher and a tool that declares an effect
- **WHEN** the researcher runs
- **THEN** the effecting tool is not among the tools it is offered
- **AND** the plugin is told which of its tools was withheld

#### Scenario: A sub-agent cannot stop the turn to ask

- **GIVEN** a delegated loop, running
- **WHEN** the tools it may call are read
- **THEN** nothing among them stops the turn, and nothing among them writes

#### Scenario: The rule is asserted rather than described

- **GIVEN** the tools a delegated loop is offered, whatever was passed to it
- **WHEN** a guard reads them
- **THEN** it fails if any writes, stops the turn, or declares an effect

### Requirement: The travel scope ships a researcher

The travel scope SHALL offer a tool that researches a question over several lookups and
answers with one report. How many rounds it may spend SHALL be the deployment's to set,
read from the plugin's own settings.

#### Scenario: A broad question is researched rather than answered in one pass

- **GIVEN** the travel scope, with its documents and its forecast tool
- **WHEN** a question needs several lookups
- **THEN** the researcher runs a loop of its own, and the answer rests on what it found

#### Scenario: The conversation carries the report

- **GIVEN** a turn whose researcher made several lookups
- **WHEN** what the turn's model was told is read
- **THEN** it holds the report, and not each lookup that produced it

#### Scenario: The trace holds what the conversation does not

- **GIVEN** the same turn
- **WHEN** its trace is read
- **THEN** the researcher's lookups are there, nested under the call that started them

#### Scenario: The rounds are the deployment's to set

- **GIVEN** a deployment naming a number of rounds in the plugin's own settings
- **WHEN** the researcher runs
- **THEN** it spends no more than that, and no more than the host allows either
