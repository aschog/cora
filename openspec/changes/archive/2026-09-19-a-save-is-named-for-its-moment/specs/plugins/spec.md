As someone training,\
I want each save named for the moment I saved it,\
so that every workout has an entry of its own and the day reads in order.

## MODIFIED Requirements

### Requirement: A finished workout is a document of the fitness field

Finishing a workout SHALL upload it into the fitness field as a Markdown document named
for the moment it was saved, the day first and the time behind it. The text SHALL be a
heading per exercise carrying its load, followed by the sets it took. An exercise
nothing was logged for SHALL NOT appear.

#### Scenario: A workout is finished

- **GIVEN** a workout with sets logged against one exercise
- **WHEN** the reader finishes it
- **THEN** a document named for today and the time is in the fitness field, holding
  that exercise and its sets

#### Scenario: Two saves on one day

- **GIVEN** a workout finished twice on one day
- **WHEN** the field is listed in the rail
- **THEN** it holds two documents, each named for its own moment

#### Scenario: An exercise that was not worked

- **GIVEN** a workout where one planned exercise logged nothing
- **WHEN** it is finished
- **THEN** the document does not name that exercise

#### Scenario: Nothing logged at all

- **WHEN** the reader finishes a workout with no set logged
- **THEN** nothing is uploaded

### Requirement: The coach lists the workouts

The fitness field SHALL offer a tool listing every workout logged in it, as text ready to
show. A session SHALL be one day, dated from the document's name whether or not a time
follows the day, oldest first, and a day's saves SHALL come in the order of their
names. Unasked for detail, a session SHALL name the exercises worked, as the log spells
them, each once. Asked for detail, each movement SHALL carry its load, sets, reps and
volume. The list SHALL narrow to one exercise, matched whatever its case, and to
sessions since a day. A document not named for a day SHALL NOT be a session. One the
grammar cannot read SHALL be left out, with a line on the trace.

#### Scenario: Every workout

- **GIVEN** three workouts saved into the fitness field, two on one day
- **WHEN** the coach is asked what was trained
- **THEN** the answer is two lines, a day and its exercises each, and no number

#### Scenario: A day's saves in the order they happened

- **GIVEN** two saves of one day, the later one uploaded first
- **WHEN** the coach is asked for the details
- **THEN** the earlier save's movements come first

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
