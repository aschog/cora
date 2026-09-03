As a person whose agent can change things,\
I want to see what it is about to do and approve it first,\
so that no effect cora is asked for happens without me.

## Purpose

What cora may change outside itself, and the approval that has to come first: how a
proposed effect is shown, how it is approved or declined, and where what it produces is
kept.

## ADDED Requirements

### Requirement: An effect waits for approval before it happens

A tool declaring that it changes something outside cora SHALL NOT run on the model's
word alone. The system SHALL state what the call would do and the arguments it was
asked for, and SHALL wait. Nothing outside cora SHALL change before the answer comes
back. Once the call is approved it SHALL run, and the turn's trace SHALL hold both the
approval and the call it authorised.

#### Scenario: An effect is proposed and waits

- **GIVEN** a scope holding a tool that changes something outside cora
- **WHEN** the model asks to call it
- **THEN** the turn stops, and what it says it will do is put to the user
- **AND** the tool has not run

#### Scenario: An approved effect happens

- **GIVEN** a turn stopped on such a proposal
- **WHEN** it is approved
- **THEN** the tool runs, the turn is answered, and the trace holds the approval and the
  call

#### Scenario: A tool that declares nothing is not gated

- **GIVEN** a tool registered without the declaration
- **WHEN** the model calls it
- **THEN** it runs in the round it was asked for, and the turn never stops

### Requirement: A declined effect changes nothing, and the turn says so

Declining SHALL leave everything outside cora as it was, and the declined call SHALL
never run. The turn SHALL still be answered, and the answer SHALL say what it did not
do.

#### Scenario: Declining stops the call

- **GIVEN** a turn stopped on a proposal
- **WHEN** it is declined
- **THEN** the tool does not run, and nothing outside cora has changed

#### Scenario: The answer names what was refused

- **GIVEN** the same turn, declined
- **WHEN** it finishes
- **THEN** the answer says the effect did not happen, and the trace records the decline

### Requirement: Every approval a round needs is settled before the round runs

A round proposing more than one effect SHALL have each of them approved or declined
before any of them runs. Picking a turn up after it stopped SHALL NOT run anything that
already ran. Each approved effect SHALL happen exactly once.

#### Scenario: Two effects in one turn

- **GIVEN** a turn in which the model proposes two effects
- **WHEN** the first is approved and then the second
- **THEN** each ran exactly once, and neither ran before both were settled

#### Scenario: One approved and one declined

- **GIVEN** a round proposing two effects
- **WHEN** one is approved and the other declined
- **THEN** only the approved one ran, and the model is told about both

### Requirement: The gate is cora's own and cannot be removed

The gate SHALL be a step of the core, standing on the only path from the model to its
tools, so no call reaches a tool without passing it. A plugin SHALL NOT be able to
unsubscribe it, subscribe to it, or imitate it, and no handler SHALL be able to stop a
turn. The gate SHALL cover what is declared to cora, which is every tool a plugin
registered.

#### Scenario: A plugin cannot switch the gate off

- **GIVEN** a plugin subscribing to every point in the turn it may
- **WHEN** its own effecting tool is called
- **THEN** the gate still stops the turn, whatever its handlers returned

#### Scenario: No path reaches a tool without the gate

- **WHEN** the walk a turn takes is read
- **THEN** the tools are reached through the gate and through nothing else

#### Scenario: A handler cannot stop a turn

- **WHEN** what a handler may return is read
- **THEN** it can refuse or amend, and there is nothing it can answer that pauses

### Requirement: What an effect produces is a file the user keeps

An approved effect that produces something SHALL write it as a file under one output
location the deployment configures, outside the directories cora keeps its own stores
in. A plugin SHALL be handed that location rather than choosing one, and a name that
would put the file outside it SHALL be refused. `README.md` SHALL say where the location
is and how to move it.

#### Scenario: The result exists as a file

- **GIVEN** an approved effect that produces an itinerary
- **WHEN** it completes
- **THEN** the file is under the configured output location, and its text is what was
  produced

#### Scenario: The location is the deployment's to move

- **GIVEN** a deployment naming an output location of its own
- **WHEN** an effect writes
- **THEN** the file lands there, and the default is used where nothing is named

#### Scenario: A name cannot escape the location

- **GIVEN** a plugin writing under a name that climbs out of the directory
- **WHEN** it writes
- **THEN** the write is refused, and nothing is written outside the location

### Requirement: The travel scope can save an itinerary

The travel scope SHALL offer a tool that saves an itinerary as a file, declared as
changing something outside cora. Calling it SHALL therefore stop the turn for approval
like any other effect.

#### Scenario: An itinerary is saved after approval

- **GIVEN** a turn in the travel field that has worked out an itinerary
- **WHEN** the model asks to save it and the user approves
- **THEN** the itinerary is a file under the output location, and the answer says where

#### Scenario: The tool says it has an effect

- **WHEN** the plugins are listed
- **THEN** the itinerary tool is shown as having an effect, under the travel scope

### Requirement: The page shows what cora is about to do

The page SHALL draw a stopped turn as what the call would do, the arguments it carries,
and a way to approve or decline. A page reopened while a turn is stopped SHALL find the
proposal still outstanding and draw it. An answered proposal SHALL be shown as settled,
saying which way it went.

#### Scenario: The proposal is drawn

- **GIVEN** a turn stopped on a proposal
- **WHEN** the page draws it
- **THEN** it shows what the call would do and the arguments, with an approve and a
  decline

#### Scenario: A reload finds the proposal

- **GIVEN** a turn stopped on a proposal, and the page reloaded
- **WHEN** the conversation is reopened
- **THEN** the proposal is still there to answer

#### Scenario: An answered proposal reads as settled

- **GIVEN** a proposal the reader approved
- **WHEN** the rest of the turn arrives
- **THEN** the card says it was approved, in the place the proposal stood
