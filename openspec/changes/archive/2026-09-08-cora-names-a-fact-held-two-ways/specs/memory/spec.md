As a returning reader,\
I want cora to notice when its notes hold one thing about me at several values,\
so that an answer turning on it is asked about rather than guessed at.

## ADDED Requirements

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
