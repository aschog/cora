# conversation Specification

## Purpose

How a turn runs: the steps it walks, the order it walks them in, and what it reports
about where it got to.

## Requirements

### Requirement: A turn walks named steps

The system SHALL run a turn as an ordered sequence of named steps. *screen* admits the
question and opens the turn. *work* reaches for the model and its tools. *answer*
settles what the user reads. The system SHALL report the steps, named, in the order
walked.

#### Scenario: A turn names the steps it walked

- **GIVEN** any question
- **WHEN** the turn runs
- **THEN** its steps name *screen*, *work* and *answer*, in that order

#### Scenario: The question is screened before the model is reached

- **GIVEN** a question a rule refuses
- **WHEN** the turn runs
- **THEN** the refusal comes out of the screening step, and no model was called

#### Scenario: The model's rounds are spent in the working step

- **GIVEN** a question the model answers only after calling tools twice
- **WHEN** the turn runs
- **THEN** every round falls inside the working step, and the steps either side take none

#### Scenario: A failure is reported as the failing step's

- **GIVEN** a turn whose model is unreachable
- **WHEN** the failure arrives
- **THEN** it names the step it came out of, and the sentence the user reads is unchanged
- **AND** the next question on that thread is answered
