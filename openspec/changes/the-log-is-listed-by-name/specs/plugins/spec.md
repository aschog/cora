As someone training,\
I want the coach to name my workouts and give the numbers only when I ask,\
so that the answer is short and every figure in it is the tool's.

## MODIFIED Requirements

### Requirement: The coach lists the workouts

The fitness field SHALL offer a tool listing every workout logged in it, as text ready to
show. A session SHALL be one day, dated from the document's name, oldest first. Unasked
for detail, a session SHALL name the exercises worked, as the log spells them, each once.
Asked for detail, each movement SHALL carry its load, sets, reps and volume. The list
SHALL narrow to one exercise, matched whatever its case, and to sessions since a day. A
document not named for a day SHALL NOT be a session. One the grammar cannot read SHALL
be left out, with a line on the trace.

#### Scenario: Every workout, by name

- **GIVEN** three workouts saved into the fitness field, two on one day
- **WHEN** the coach is asked what was trained
- **THEN** the answer is two lines, a day and its exercises each, and no number

#### Scenario: The numbers, on request

- **GIVEN** the same workouts
- **WHEN** the reader asks for the details
- **THEN** each movement is shown with its load, sets, reps and volume

#### Scenario: One exercise over time

- **GIVEN** workouts on three days, two of them with the deadlift
- **WHEN** the coach is asked about the deadlift in detail
- **THEN** the answer has those two days with reps and volume, and marks where it rose

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
- **THEN** it is listed as any other, its names as the log spells them

### Requirement: The numbers are the tool's

Reps and volume SHALL be computed by the tool. Volume SHALL be load times reps for a
load in kilograms, and absent for a bodyweight load. The brief SHALL tell the coach to
show the tool's text as it is, names untranslated, and to ask for detail only when the
reader asks for numbers.

#### Scenario: Volume of a loaded movement

- **GIVEN** a movement of 3 sets of 10 at 14 kg
- **WHEN** it is listed in detail
- **THEN** it carries 30 reps and 420 kg

#### Scenario: A bodyweight movement

- **GIVEN** a movement at bodyweight
- **WHEN** it is listed in detail
- **THEN** it carries its reps and no volume

#### Scenario: The brief relays

- **WHEN** the fitness brief is read
- **THEN** it says to pass the listing on as it is, untranslated, and detail only on request
