As a lifter,\
I want my watch to start the workout on the page and finish it when I am done,\
so that training and logging are one thing rather than two.

## ADDED Requirements

### Requirement: The fitness field brings a screen for the wrist

The fitness plugin SHALL bring a workout extension: one screen added to a sport in the
watch's own workout app. While the workout runs, the screen SHALL show the workout's
elapsed time, and SHALL carry one control that finishes the workout on the page. The
screen SHALL say whether cora took what it last wrote, so a link that is down is read on
the wrist rather than found later.

#### Scenario: The screen is looked at

- **GIVEN** the extension added to a sport, and that sport started
- **WHEN** the lifter swipes to the screen
- **THEN** it shows the workout's elapsed time and that cora is linked

#### Scenario: Cora cannot be reached

- **GIVEN** the same screen, and a cora the phone cannot reach
- **WHEN** it writes
- **THEN** the screen says the link is down, and the workout is unaffected

### Requirement: The watch tells the field what it is doing

The screen SHALL write the fitness field's notice when it opens, saying a workout is
running, and again when its control is tapped, saying the workout is finished. Nothing
else SHALL be written, and a write that fails SHALL NOT be retried in a way that blocks
the screen.

#### Scenario: The workout begins

- **GIVEN** a sport carrying the extension
- **WHEN** the workout is started and its screen is created
- **THEN** the fitness field's notice says a workout is running

#### Scenario: The control is tapped

- **WHEN** the lifter taps the control on that screen
- **THEN** the fitness field's notice says the workout is finished

### Requirement: The trainer follows the watch

The trainer page SHALL ask the fitness field for its notice every few seconds. A notice
saying a workout is running, taken after the workout the page holds began, SHALL become
that workout's start, and the page SHALL show the time running from it. A notice older
than the page's own workout SHALL be ignored. With no notice, or with nothing answering,
the page SHALL work exactly as it does without a watch.

#### Scenario: The watch starts the workout

- **GIVEN** the trainer drawn, and a notice taken after its workout began saying one is running
- **WHEN** the page reads it
- **THEN** the workout's start becomes the notice's, and the page shows the time running

#### Scenario: Last workout's notice

- **GIVEN** a notice taken before the page's own workout began
- **WHEN** the page reads it
- **THEN** it is ignored, and the workout keeps the start it had

#### Scenario: No watch

- **GIVEN** a field whose notice nobody has written
- **WHEN** the trainer is worked and finished on the page
- **THEN** everything happens as it does without a watch

### Requirement: A tap on the wrist saves the workout

Reading a notice that says the workout is finished, the page SHALL finish the workout
without asking and upload it as finishing on the page does, and SHALL say that the watch
ended it. It SHALL act on one such notice once, however many times it reads it. Where no
set was logged, nothing SHALL be uploaded and the page SHALL say so.

#### Scenario: The workout is saved from the wrist

- **GIVEN** a workout with sets logged, and a notice saying it is finished
- **WHEN** the page reads it
- **THEN** the workout is uploaded to the fitness field, a fresh workout starts, and the
  page says the watch ended it

#### Scenario: Read again

- **GIVEN** the same notice still held by the field
- **WHEN** the page reads it again
- **THEN** nothing further is saved and the fresh workout is left alone

#### Scenario: Nothing logged

- **GIVEN** a workout with no set logged, and a notice saying it is finished
- **WHEN** the page reads it
- **THEN** nothing is uploaded and the page says so

### Requirement: The watch app is built with cora's address

The build SHALL bake into the app the address at which the phone can reach cora, and
SHALL hand the app to the Zepp tooling for installation. The address SHALL default to
this machine's name on the network and SHALL be overridable. Without the Zepp tooling
the build SHALL stop and name the command that installs it.

#### Scenario: Building it

- **WHEN** the watch app is built
- **THEN** it carries the address of the cora it is to write to

#### Scenario: The tooling is missing

- **WHEN** the Zepp command line tool is not installed
- **THEN** the build stops and names the command that installs it
