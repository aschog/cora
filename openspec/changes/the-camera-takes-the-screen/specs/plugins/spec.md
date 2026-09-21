As someone training,\
I want the camera to take the whole screen with the controls on it,\
so that I film myself full size and still log the set.

## MODIFIED Requirements

### Requirement: The fitness field brings a trainer

The fitness plugin SHALL bring its field a page: a plan of exercises worked one at a
time, each with its sets, its weight and whatever clips it has, and a camera to film
against. An exercise's row SHALL carry its number and its name, and no count of sets or
weight. The weight SHALL move one kilogram a tap, and never below one. While the camera
shows, its picture SHALL fill the page. The history, the finish, the exercise row, the
sets and the weight SHALL be drawn over it. The mirror and pose controls, the set count
and the rest SHALL keep their place between the row and the sets. With both rails of the
screen folded, the picture SHALL be the whole screen until the camera closes. A picture
taken away SHALL close the camera. The plan SHALL be read from the sheet the page names, and the page SHALL hand what it produces to cora and
to nothing else. Every other address it reaches SHALL be one written down, so a new one
is a change somebody made rather than a change nobody saw.

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

#### Scenario: The camera is opened

- **GIVEN** the trainer drawn, on a device with a camera
- **WHEN** the reader opens the camera
- **THEN** its picture fills the page, with the buttons, the row, the sets and the weight
  drawn over it

#### Scenario: A set is logged while filming

- **GIVEN** the camera filling the page
- **WHEN** the reader logs a set
- **THEN** it reads as done over the picture, and the rest counts down between the row and
  the sets

#### Scenario: The camera with the rails folded

- **GIVEN** the trainer drawn with both rails folded, on a device with a camera
- **WHEN** the reader opens the camera
- **THEN** its picture is the whole screen, and closing the camera gives the rails their
  place back

#### Scenario: The picture is taken away

- **GIVEN** the camera filling the screen
- **WHEN** the device takes the picture away
- **THEN** the camera closes, and the rails have their place back

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names
