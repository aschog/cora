As someone whose training plan changes week to week,\
I want the trainer to follow the sheet I keep it in,\
so that a row I edit is what I am asked to do next time I open it.

## MODIFIED Requirements

### Requirement: The fitness field brings a trainer

The fitness plugin SHALL bring its field a page: a plan of exercises worked one at a
time, each with its sets, its weight and whatever clips it has, and a camera to film
against. The plan SHALL be read from the sheet the page names, and the page SHALL hand
what it produces to cora and to nothing else. Every other address it reaches SHALL be one
written down, so a new one is a change somebody made rather than a change nobody saw.

#### Scenario: The field is opened

- **GIVEN** the fitness plugin loaded
- **WHEN** the reader asks what fields have a page
- **THEN** fitness is named with the path its trainer is served under

#### Scenario: The trainer is worked

- **GIVEN** the trainer drawn
- **WHEN** the reader logs a set of the current exercise
- **THEN** that set reads as done, and the count on that exercise says so

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names

## ADDED Requirements

### Requirement: The plan is the sheet's, and the page's when the sheet is not there

The trainer SHALL read its plan from the sheet each time it is opened, taking each row's
exercise, sets, reps, weight and clips. A row naming no exercise SHALL be skipped. Where
the sheet cannot be read, the plan last read SHALL stand, and failing that the one written
into the page — and the reader SHALL be told which of those they are training from.

#### Scenario: A sheet is read

- **GIVEN** a sheet whose rows name exercises, their sets, their reps and their weights
- **WHEN** the page reads it
- **THEN** the plan is those rows, in that order

#### Scenario: A row that names no exercise

- **GIVEN** a sheet carrying an empty row between two exercises
- **WHEN** the page reads it
- **THEN** that row is not an exercise of the plan

#### Scenario: The sheet cannot be reached

- **GIVEN** a trainer opened with no way to reach the sheet
- **WHEN** it is drawn
- **THEN** it is drawn from the plan the page ships with, and says so

### Requirement: Progress survives a plan that changed under it

Where a sheet is read while a workout is under way, an exercise still in the plan SHALL
keep the sets logged against it.

#### Scenario: The sheet changed mid-workout

- **GIVEN** a workout with sets logged, and a sheet that adds an exercise
- **WHEN** the new plan is adopted
- **THEN** what was logged against the exercises still in it is still logged
