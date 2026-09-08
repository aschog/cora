# memory Specification

## Purpose

What cora keeps about a reader between sessions, and what taking any of it back asks of
them first: the control on a fact's row, and the question it raises before anything is
forgotten.

## Requirements

### Requirement: Forgetting a fact is asked about first

Forgetting SHALL be confirmed before it happens. The system SHALL put the question over
the page, naming the fact and saying what is lost and what is not. Nothing SHALL be
forgotten until it is confirmed, and keeping the fact SHALL leave it exactly as it was.

#### Scenario: The control asks rather than forgets

- **GIVEN** a fact cora is holding
- **WHEN** the control on its row is used
- **THEN** the reader is asked, and the fact is still held

#### Scenario: A confirmed forget happens

- **GIVEN** that question open
- **WHEN** it is confirmed
- **THEN** the fact is forgotten and gone from the rail

#### Scenario: Keeping the fact forgets nothing

- **GIVEN** that question open
- **WHEN** the reader keeps the fact instead
- **THEN** nothing is forgotten, and the fact is still listed

### Requirement: Forgetting everything is asked about too

Forgetting everything SHALL be confirmed the same way, and SHALL say that it is every
fact rather than one.

#### Scenario: Everything is asked about before it goes

- **GIVEN** two facts cora is holding
- **WHEN** forgetting everything is used
- **THEN** the reader is asked, and both facts are still held

#### Scenario: Confirming empties the rail

- **GIVEN** that question open
- **WHEN** it is confirmed
- **THEN** every fact is forgotten

### Requirement: A fact's row carries the same control a conversation's does

The system SHALL draw a fact's row as it draws a conversation's: the fact, and one
control at the end of it, named for what it would forget. Neither the control nor the
question SHALL be the colour the system reserves for a quoted passage.

#### Scenario: The control is named for its fact

- **GIVEN** two facts cora is holding
- **WHEN** the rail is drawn
- **THEN** each control is named for the fact it would forget, and neither is a word

### Requirement: A fact leaves the rail when the reader confirms it

The rail SHALL stop listing a fact as soon as the reader confirms forgetting it, before
the store has answered. Forgetting everything SHALL empty the rail the same way.

#### Scenario: The row goes before the store answers

- **GIVEN** a fact the reader has confirmed forgetting
- **WHEN** the store has not yet answered
- **THEN** the rail no longer lists it, and lists the others

#### Scenario: Forgetting everything empties it

- **GIVEN** a reader who has confirmed forgetting everything
- **WHEN** the store has not yet answered
- **THEN** the rail lists nothing

### Requirement: A fact the store would not forget comes back, with the reason

Where the store refuses, the fact SHALL be listed again and the page SHALL say why.

#### Scenario: Refused, so it is listed again

- **GIVEN** a fact the reader confirmed forgetting
- **WHEN** the store refuses
- **THEN** it is listed again, and the page says why

### Requirement: A fact held at several values is named as one

Where the facts cora holds carry one subject at two or more different values, the brief
SHALL say so — naming the subject and how many values it is held at — and SHALL tell the
model to settle it with the ask tool, offering those values, rather than picking one
itself or writing one into a card asking about something else.

Cora SHALL find the conflict itself rather than requiring the model to notice it. Whether
a given answer turns on the conflicted fact remains the model's to judge, so the brief
SHALL state the conflict and leave the asking conditional on it mattering.

A subject SHALL be read as the words a fact opens with before its first figure, so notes
disagreeing about a number are found. A fact contradicted in prose alone is not found,
and the brief SHALL say nothing about it.

The section SHALL be absent where there is nothing to settle, including where two notes
share a subject and agree on its value.

#### Scenario: Three values for one subject are reported

- **GIVEN** cora holds "bodyweight 77 kg", "bodyweight 75 kg" and "bodyweight 85 kg"
- **WHEN** a turn's brief is built
- **THEN** it names `bodyweight` as held at 3 different values, and names the ask tool

#### Scenario: Notes that agree are not reported

- **GIVEN** cora holds "bodyweight 75 kg, from the coach notes" and "bodyweight 75 kg,
  from the intake form"
- **WHEN** a turn's brief is built
- **THEN** no conflict is reported

#### Scenario: A subject held once is not reported

- **GIVEN** cora holds one note about bodyweight and one about training days
- **WHEN** a turn's brief is built
- **THEN** no conflict is reported
