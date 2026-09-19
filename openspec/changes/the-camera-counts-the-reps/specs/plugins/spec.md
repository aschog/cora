As someone training,\
I want the camera to count my reps while I lift,\
so that I can watch the count instead of keeping it in my head.

## MODIFIED Requirements

### Requirement: The fitness field brings a trainer

The fitness plugin SHALL bring its field a page: a plan of exercises worked one at a
time, each with its sets, its weight and whatever clips it has, and a camera to film
against. An exercise's row SHALL carry its number and its name, and no count of sets or
weight. The weight SHALL move one kilogram a tap, and never below one. With the pose
overlay on, the trainer SHALL count repetitions from what the camera sees, and show the
running count over the frame. It SHALL count any repeated movement the hands make
against the torso, or the torso against planted hands, without naming an exercise. It
SHALL count nothing while a rest is running. The count SHALL be a readout: it SHALL
leave every set's reps untouched, and SHALL start again at nought when a set is logged,
when the exercise changes, and when cora takes the workout.
The plan SHALL be read from the sheet the page names, and the page SHALL hand what it
produces to cora and to nothing else. Every other address it reaches SHALL be one written
down, so a new one is a change somebody made rather than a change nobody saw.

#### Scenario: The field is opened

- **GIVEN** the fitness plugin loaded
- **WHEN** the reader asks what fields have a page
- **THEN** fitness is named with the path its trainer is served under

#### Scenario: The trainer is worked

- **GIVEN** the trainer drawn
- **WHEN** the reader logs a set of the current exercise
- **THEN** that set reads as done, and the exercise reads complete once all its sets do

#### Scenario: The weight is adjusted

- **GIVEN** the trainer drawn on an exercise with a weight
- **WHEN** the reader taps the weight up once
- **THEN** it reads one kilogram more

#### Scenario: A row is the exercise

- **WHEN** the rows are read
- **THEN** each carries its number and its name, and no count of sets or weight

#### Scenario: The camera counts the reps

- **GIVEN** the pose overlay on
- **WHEN** the lifter repeats a movement in front of the camera
- **THEN** the count over the frame rises by one a repetition

#### Scenario: The exercise is not named

- **GIVEN** a movement where the hands stay put and the body travels
- **WHEN** it is repeated in front of the camera
- **THEN** it counts the same as a movement the hands make

#### Scenario: A movement the torso carries whole

- **GIVEN** a movement in which the hands ride with the torso
- **WHEN** it is repeated in front of the camera
- **THEN** nothing is counted, because nothing moved against the torso

#### Scenario: A rest is not counted through

- **GIVEN** a set logged and its rest running
- **WHEN** the lifter moves in front of the camera
- **THEN** the count stands at nought until the rest is over

#### Scenario: Stillness is not counted

- **GIVEN** the pose overlay on
- **WHEN** the lifter stands still, or walks across the frame
- **THEN** the count does not rise

#### Scenario: The count is a readout

- **GIVEN** a count standing over the frame
- **WHEN** the reader reads the sets
- **THEN** their reps are what the plan and the taps left them

#### Scenario: The count starts again

- **GIVEN** a count standing over the frame
- **WHEN** a set is logged, or the exercise changes, or cora takes the workout
- **THEN** the count reads nought

#### Scenario: A set taken back is not a set logged

- **GIVEN** a set logged and a count standing over the frame
- **WHEN** that same set is tapped again to undo it
- **THEN** the count is left where it was

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names
