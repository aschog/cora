# trace Specification

## Purpose

What a turn did, in the order it did it: the model's decisions and the tool calls behind
an answer, so the work can be watched as it happens and read back afterwards.

## Requirements

### Requirement: A turn reports every step it takes

The system SHALL record each step of a turn — what the model decided, what tools it
called — and SHALL return those steps with the answer.

#### Scenario: The trace shows each step

- **WHEN** a turn calls a tool and answers
- **THEN** its steps name the model's decision and the tool call, in the order taken

### Requirement: A tool step carries its arguments and its result

The system SHALL show, for each tool call, the name called, the arguments given and what
came back.

#### Scenario: A tool call is read back

- **GIVEN** a turn that searched the documents
- **WHEN** its steps are read
- **THEN** the search step carries the arguments the model wrote and the result it got

### Requirement: A step is reported as it is taken

The system SHALL report each step to the caller the moment the run takes it, so work in
progress can be shown, and SHALL keep the steps already reported when a run fails
part-way.

#### Scenario: A run fails mid-turn

- **GIVEN** a turn that fails after calling a tool
- **WHEN** the failure arrives
- **THEN** the steps reported before it stand

### Requirement: A turn's trace is that turn's alone

The system SHALL return, for a turn on a thread that has already taken others, only the
steps of the turn just taken.

#### Scenario: A later turn on a long thread

- **GIVEN** a thread carrying earlier turns and their steps
- **WHEN** a new question is answered on it
- **THEN** the steps returned are that turn's, not the thread's

### Requirement: A step that went wrong says so

The system SHALL mark a step that records a failure as failed, so a trace distinguishes
work that succeeded from work that did not.

#### Scenario: A tool that refused

- **GIVEN** a turn whose tool call was refused
- **WHEN** its steps are read
- **THEN** that step is marked as failed and carries the reason
