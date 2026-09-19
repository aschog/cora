As someone training,\
I want each save to carry the name of the workout I trained,\
so that the coach can name my workouts rather than list their lifts.

## MODIFIED Requirements

### Requirement: A finished workout is a document of the fitness field

Finishing a workout SHALL upload it into the fitness field as a Markdown document named
for the moment it was saved, the day first and the time behind it. The text SHALL open
with the workout's name, taken from the sheet the plan was read from, where the plan came
from a sheet. Below it SHALL be a heading per exercise carrying its load, followed by
the sets it took. An exercise nothing was logged for SHALL NOT appear.

#### Scenario: A workout is finished

- **GIVEN** a workout with sets logged against one exercise
- **WHEN** the reader finishes it
- **THEN** a document named for today and the time is in the fitness field, holding
  that exercise and its sets

#### Scenario: The save says which workout it was

- **GIVEN** a plan read from a sheet whose tab is named
- **WHEN** the reader finishes a workout
- **THEN** the document's first line is that name

#### Scenario: The plan written into the page

- **GIVEN** no sheet reachable and no plan cached
- **WHEN** the reader finishes a workout
- **THEN** the document opens with its first exercise, and no name

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
names. Unasked for detail, a session SHALL name the workouts trained, each once, and the
exercises of a save that carries no name. Asked for detail, a day's line SHALL carry its
workouts' names, and each movement SHALL carry its load, sets, reps and volume. The list
SHALL narrow to one exercise, matched whatever its case, and to sessions since a day. A
document not named for a day SHALL NOT be a session. One the grammar cannot read SHALL
be left out, with a line on the trace.

#### Scenario: Every workout

- **GIVEN** three workouts saved into the fitness field, two on one day, each titled
- **WHEN** the coach is asked what was trained
- **THEN** the answer is two lines, a day and its workouts' names each, and no number

#### Scenario: A save without a name

- **GIVEN** a day with a titled save and an untitled one
- **WHEN** the coach is asked what was trained
- **THEN** the day names the workout, and the untitled save's exercises beside it

#### Scenario: A day's saves in the order they happened

- **GIVEN** two saves of one day, the later one uploaded first
- **WHEN** the coach is asked for the details
- **THEN** the earlier save's movements come first

#### Scenario: The numbers, on request

- **GIVEN** the same workouts
- **WHEN** the reader asks for the details
- **THEN** the day's line carries the workout's name, and each movement its load, sets,
  reps and volume

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
