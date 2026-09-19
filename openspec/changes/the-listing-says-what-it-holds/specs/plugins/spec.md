As someone training,\
I want the coach's summary to say what it is and what else is on file,\
so that it never tells me the log holds less than it does.

## MODIFIED Requirements

### Requirement: The numbers are the tool's

Reps and volume SHALL be computed by the tool. Volume SHALL be load times reps for a
load in kilograms, and absent for a bodyweight load. Unasked for detail, the listing
SHALL put a day's workouts before an untitled save's lifts, mark those lifts as an
untitled save's, and close with how many days and saves it holds and that the numbers
are in the details. The brief SHALL tell the coach to show the tool's text as it is,
names untranslated, to add nothing about what the log holds or lacks, and to ask for
detail only when the reader asks for numbers.

#### Scenario: Volume of a loaded movement

- **GIVEN** a movement of 3 sets of 10 at 14 kg
- **WHEN** it is listed in detail
- **THEN** it carries 30 reps and 420 kg

#### Scenario: A bodyweight movement

- **GIVEN** a movement at bodyweight
- **WHEN** it is listed in detail
- **THEN** it carries its reps and no volume

#### Scenario: The names view says what it is

- **GIVEN** a day with a titled save and an untitled one
- **WHEN** the workouts are listed without detail
- **THEN** the day names the workout first, then the untitled save's lifts marked as
  such, and the last line counts one day and two saves and points to the details

#### Scenario: The brief relays

- **WHEN** the fitness brief is read
- **THEN** it says to pass the listing on as it is, untranslated, to add nothing about
  what the log holds or lacks, and detail only on request
