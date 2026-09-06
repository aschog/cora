As a reader,\
I want a document I have confirmed away to leave the rail when I say so,\
so that the click does not read as having missed.

## Purpose

When a deleted document leaves the rail, and what the page does when the store refuses.

## ADDED Requirements

### Requirement: A document leaves the rail when the reader confirms it

The rail SHALL stop listing a document as soon as the reader confirms deleting it, before
the store has answered.

#### Scenario: The row goes before the store answers

- **GIVEN** a document the reader has confirmed deleting
- **WHEN** the store has not yet answered
- **THEN** the rail no longer lists it, and lists the others

### Requirement: A document the store would not delete comes back, with the reason

Where the store refuses the delete, the document SHALL be listed again and the page SHALL
say why.

#### Scenario: Refused, so it is listed again

- **GIVEN** a document the reader confirmed deleting
- **WHEN** the store refuses
- **THEN** it is listed again, and the page says why
