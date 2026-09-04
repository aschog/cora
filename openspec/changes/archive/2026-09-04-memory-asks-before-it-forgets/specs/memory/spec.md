As a reader,\
I want the memory rail to ask before it forgets,\
so that a fact I told cora is not one click from gone.

## Purpose

What cora keeps about a reader between sessions, and what taking any of it back asks of
them first: the control on a fact's row, and the question it raises before anything is
forgotten.

## ADDED Requirements

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
