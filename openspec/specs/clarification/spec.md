# clarification Specification

## Purpose

What cora does when it cannot tell: rather than picking one reading of an ambiguous
question, the turn stops, puts the choice to the user, and finishes on what they pick.

## Requirements

### Requirement: A turn stops rather than guessing

The system SHALL stop a turn when the model cannot tell which of several readings was
meant, and SHALL hand back the question it stopped on together with the options it is
choosing between.

#### Scenario: A fact recalled three ways

- **GIVEN** a question whose answer depends on which of three remembered values is meant
- **WHEN** the turn runs
- **THEN** it stops, and the choice is put to the user with each option and where it
  came from

### Requirement: A stopped turn has no answer until it is resumed

The system SHALL report a stopped turn as stopped rather than as answered, and SHALL not
record it until it has an answer.

#### Scenario: A turn stops

- **WHEN** a turn stops to ask
- **THEN** no answer is returned, and nothing is recorded for that turn

### Requirement: The turn finishes on what the user picked

The system SHALL resume a stopped turn on the option chosen, SHALL answer using it, and
SHALL record the finished turn under the question it originally opened with.

#### Scenario: The pick answers the question

- **GIVEN** a turn stopped on a choice
- **WHEN** an option is picked
- **THEN** the turn finishes using it, recorded under the question that raised it

#### Scenario: Declining is a way out

- **GIVEN** a turn stopped on a choice
- **WHEN** the user declines rather than picking
- **THEN** the turn finishes without choosing, and the conversation is intact

### Requirement: A caller arriving later can find the open choice

The system SHALL let a caller ask what a thread is waiting on, so a page reloaded while
a choice was open can draw it again.

#### Scenario: The page is reloaded mid-choice

- **GIVEN** a thread with a turn stopped on a choice
- **WHEN** a fresh caller asks what that thread is waiting on
- **THEN** the open choice comes back

#### Scenario: A thread waiting on nothing

- **WHEN** a caller tries to resume a thread that is not waiting
- **THEN** it is refused, because there is nothing to resume
