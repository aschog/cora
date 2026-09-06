As a reader,\
I want a fact I have confirmed away to leave the rail when I say so,\
so that the click does not read as having missed.

## Purpose

When a forgotten fact leaves the rail, and what the page does when the store refuses.

## ADDED Requirements

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
