As someone training,\
I want the finish button to say where the workout stands,\
so that the trainer stays the trainer and I still know.

## MODIFIED Requirements

### Requirement: A finished workout is a document of the fitness field

Finishing a workout SHALL upload it into the fitness field as a Markdown document named
for the moment it was saved, the day first and the time behind it. The finish SHALL be
offered only once a set has been logged, and the button SHALL read where the workout
stands: that no sets are logged yet, finish, or saved until the next set is logged. A
save cora took SHALL say nothing on the strip, except who ended the workout when the
watch did. The text SHALL open with the workout's
name, taken from the sheet the plan was read from, where the plan came from a sheet.
Below it SHALL be a heading per exercise carrying its load, followed by the sets it
took. An exercise nothing was logged for SHALL NOT appear.

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

- **GIVEN** a workout with no set logged
- **WHEN** the reader looks for the finish
- **THEN** it reads that no sets are logged yet, is not enabled, and nothing is uploaded
