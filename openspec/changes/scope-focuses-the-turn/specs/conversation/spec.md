## MODIFIED Requirements

### Requirement: A turn walks named steps

The system SHALL run a turn as an ordered sequence of named steps. *screen* admits the
question and opens the turn. *route* settles which scope the turn runs under. *focus*
states what cora is and what it may reach under that scope. *work* reaches for the model
and its tools. *answer* settles what the user reads. The system SHALL report the steps,
named, in the order walked.

#### Scenario: A turn names the steps it walked

- **GIVEN** any question
- **WHEN** the turn runs
- **THEN** its steps name *screen*, *route*, *focus*, *work* and *answer*, in that order

#### Scenario: The question is screened before the model is reached

- **GIVEN** a question a rule refuses
- **WHEN** the turn runs
- **THEN** the refusal comes out of the screening step, and no scope was read

#### Scenario: The brief is settled after the scope is known

- **GIVEN** a question routed into one of two scopes
- **WHEN** the turn runs
- **THEN** the brief the model reads is settled in *focus*, under the scope *route* named

#### Scenario: The model's rounds are spent in the working step

- **GIVEN** a question the model answers only after calling tools twice
- **WHEN** the turn runs
- **THEN** every round falls inside the working step, and the steps either side take none

#### Scenario: A failure is reported as the failing step's

- **GIVEN** a turn whose model is unreachable
- **WHEN** the failure arrives
- **THEN** it names the step it came out of, and the sentence the user reads is unchanged
- **AND** the next question on that thread is answered
