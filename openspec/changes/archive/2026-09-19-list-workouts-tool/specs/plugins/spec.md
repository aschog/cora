As someone training,\
I want to ask the coach what I have trained,\
so that every session I logged is in the answer, with its numbers.

## ADDED Requirements

### Requirement: The coach lists the workouts

The fitness field SHALL offer a tool listing every workout logged in it. A session SHALL
be one day, dated from the document's name, oldest first. Each movement SHALL carry its
name, load, sets, reps and volume. The list SHALL narrow to one exercise, matched
whatever its case, and to sessions since a day. A document not named for a day SHALL NOT
be a session. One the grammar cannot read SHALL be left out, with a line on the trace.

#### Scenario: Every workout

- **GIVEN** three workouts saved into the fitness field, two on one day
- **WHEN** the coach is asked what was trained
- **THEN** the answer lists two days, and the day saved twice holds both saves' movements
  in order

#### Scenario: One exercise over time

- **GIVEN** workouts on three days, two of them with the deadlift
- **WHEN** the coach is asked about the deadlift
- **THEN** the answer has those two days with reps and volume, and says whether it rose

#### Scenario: Since a day

- **WHEN** the tool is asked for sessions since a day
- **THEN** sessions before it are not listed

#### Scenario: The plan is not a workout

- **GIVEN** a training plan uploaded into the field beside the workouts
- **WHEN** the workouts are listed
- **THEN** the plan is not among them

#### Scenario: A workout the grammar refuses

- **GIVEN** a document named for a day whose text is not a workout
- **WHEN** the workouts are listed
- **THEN** it is left out, the rest are listed, and the trace names it

#### Scenario: Nothing logged

- **GIVEN** a field with no workout
- **WHEN** the workouts are listed
- **THEN** the tool says so, in words the coach can pass on

#### Scenario: A workout in any language

- **GIVEN** a workout whose exercise names are not in the coach's language
- **WHEN** the workouts are listed
- **THEN** it is listed as any other

### Requirement: The numbers are the tool's

Reps and volume SHALL be computed by the tool. Volume SHALL be load times reps for a
load in kilograms, and absent for a bodyweight load.

#### Scenario: Volume of a loaded movement

- **GIVEN** a movement of 3 sets of 10 at 14 kg
- **WHEN** it is listed
- **THEN** it carries 30 reps and 420 kg

#### Scenario: A bodyweight movement

- **GIVEN** a movement at bodyweight
- **WHEN** it is listed
- **THEN** it carries its reps and no volume

## MODIFIED Requirements

### Requirement: What the trainer logged is what cora answers from

A workout uploaded by the trainer SHALL be searched and cited as any other document of
that field is, so the reader can ask about what they lifted and be shown the day it came
from. What was trained SHALL be answered from the list rather than a search, so no
session is missed for its wording.

#### Scenario: Asking about what was lifted

- **GIVEN** a workout finished into the fitness field
- **WHEN** the reader asks about that exercise with the conversation in that field
- **THEN** the answer rests on that document and cites it

#### Scenario: Asking for everything

- **GIVEN** five workouts in the field, four of them named in another language
- **WHEN** the reader asks for all their trainings
- **THEN** the answer names every day logged
