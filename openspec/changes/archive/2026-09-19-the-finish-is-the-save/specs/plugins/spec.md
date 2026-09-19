As someone training,\
I want the workout I finish to be saved once, into the field, and read back from there,\
so that the trainer and the coach show one log and I keep nothing in the browser.

## ADDED Requirements

### Requirement: The trainer's history is the field's

The trainer SHALL keep no history of its own. History SHALL list the field's saved
workouts, read from the field by name: each save under its day and its workout's name,
with every exercise's load and reps. A fresh workout SHALL open each exercise on the
weight and the reps of the field's latest save that worked it, matched by the exercise's
name as the heading spells it, and on the plan's where none did. The page SHALL offer no
import and no export.

#### Scenario: History reads the field

- **GIVEN** a workout saved into the fitness field
- **WHEN** the reader opens History
- **THEN** that workout is listed under its day with its exercises, loads and reps, and
  the browser's storage holds no history

#### Scenario: The last weight is the field's

- **GIVEN** a save in the field with the swing at 24 kg for sets of 12
- **WHEN** a fresh workout is drawn
- **THEN** the swing opens at 24 kg with 12 reps a set

#### Scenario: An exercise never saved

- **GIVEN** a field with no save working the snatch
- **WHEN** a fresh workout is drawn
- **THEN** the snatch opens on the plan's weight and reps

#### Scenario: Nothing to carry between browsers

- **WHEN** the History is read
- **THEN** it offers no import and no export

### Requirement: A save cora did not take stands

Where the upload fails, the page SHALL say so and why, and the workout SHALL stand as it
was: its sets logged, the finish offered again. Opened outside cora, the finish SHALL
say the workout was not saved and change nothing else. The page SHALL keep no copy of
its own and SHALL offer no clipboard.

#### Scenario: The upload fails

- **GIVEN** a finished workout that cora refuses or cannot be asked
- **WHEN** the page reports it
- **THEN** it says the workout was not saved and why, the sets are still logged, and the
  finish is still offered

#### Scenario: Finished again once cora is back

- **GIVEN** a workout whose upload failed
- **WHEN** the reader finishes it again and cora takes it
- **THEN** the button reads saved and a fresh workout starts

#### Scenario: Outside cora

- **GIVEN** the page opened under no field
- **WHEN** the reader finishes a workout
- **THEN** it says the workout was not saved to cora, and nothing is uploaded

## MODIFIED Requirements

### Requirement: A finished workout is a document of the fitness field

Finishing a workout SHALL upload it into the fitness field as a Markdown document named
for the moment it was saved, the day first and the time behind it, and then for the
workout's name where the plan came from a sheet. The finish SHALL be
offered only once a set has been logged, and the button SHALL read where the workout
stands: that no sets are logged yet, finish, or saved until the next set is logged. A
save cora took SHALL say nothing on the strip, except who ended the workout when the
watch did. A fresh workout SHALL start only once cora took the save. The text SHALL open
with the workout's name, taken from the sheet the plan was read from, where the plan
came from a sheet. Below it SHALL be a heading per exercise carrying its load, followed
by the sets it took. An exercise nothing was logged for SHALL NOT appear.

#### Scenario: A workout is finished

- **GIVEN** a workout with sets logged against one exercise
- **WHEN** the reader finishes it
- **THEN** a document named for today and the time is in the fitness field, holding
  that exercise and its sets

#### Scenario: A quiet save

- **GIVEN** a workout finished from the button
- **WHEN** cora takes it
- **THEN** the button reads saved and the strip says nothing, until the next set is
  logged

#### Scenario: The save says which workout it was

- **GIVEN** a plan read from a sheet whose tab is named
- **WHEN** the reader finishes a workout
- **THEN** the document's name ends with that name, behind the moment, and its first
  line is that name

#### Scenario: The plan written into the page

- **GIVEN** no sheet reachable and no plan cached
- **WHEN** the reader finishes a workout
- **THEN** the document is named for its moment alone, and opens with its first exercise
  and no name

#### Scenario: Two saves on one day

- **GIVEN** a workout finished twice on one day
- **WHEN** the field is listed in the rail
- **THEN** it holds two documents, each named for its own moment

#### Scenario: An exercise that was not worked

- **GIVEN** a workout where one planned exercise logged nothing
- **WHEN** it is finished
- **THEN** the document does not name that exercise

#### Scenario: Nothing logged at all

- **GIVEN** a workout with no set logged
- **WHEN** the reader looks for the finish
- **THEN** it reads that no sets are logged yet, is not enabled, and nothing is uploaded

### Requirement: The coach lists the workouts

The fitness field SHALL offer a tool listing every workout logged in it, as text ready to
show. A session SHALL be one day, dated from the document's name whether or not a time,
or a time and a workout's name, follows the day, oldest first, and a day's saves SHALL
come in the order of their names. Unasked for detail, a session SHALL name the workouts
trained, each once, and the exercises of a save that carries no name. Asked for detail,
a day's line SHALL carry its workouts' names, and each movement SHALL carry its load,
sets, reps and volume. The list SHALL narrow to one exercise, matched whatever its case,
and to sessions since a day. A document not named for a day SHALL NOT be a session. One
the grammar cannot read SHALL be left out, with a line on the trace.

#### Scenario: Every workout

- **GIVEN** three workouts saved into the fitness field, two on one day, each titled
- **WHEN** the coach is asked what was trained
- **THEN** the answer is two lines, a day and its workouts' names each, and no number

#### Scenario: A save named for its moment and its workout

- **GIVEN** a document named for a day, a time and a workout
- **WHEN** the workouts are listed
- **THEN** it is a session of that day

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

## REMOVED Requirements

### Requirement: A workout that could not be saved is not lost

**Reason**: The page keeps no copy of its own any more, so there is no history to hold a
failed save and no clipboard to put it on.
**Migration**: The workout stands on the page with its sets logged and the finish offered
again, as "A save cora did not take stands" says.
