As someone training,\
I want the camera to take the whole screen with the controls on it,\
so that I film myself full size and still log the set.

## ADDED Requirements

### Requirement: A page that asks for the screen has it while the rails are folded

A page SHALL be able to tell the shell it wants the screen, and to let it go. While it
wants it and both rails are folded, the frame SHALL be drawn over everything, folded rails
included. With a rail open, or once the page lets go, the frame SHALL be drawn where it
was.

#### Scenario: Asked with both rails folded

- **GIVEN** a page drawn, and both rails folded
- **WHEN** the page asks for the screen
- **THEN** the frame is the whole screen

#### Scenario: Asked with a rail open

- **GIVEN** a page drawn beside an open rail
- **WHEN** the page asks for the screen
- **THEN** the frame is drawn where it was, and folding both rails then gives it the screen

#### Scenario: Let go

- **GIVEN** a frame that is the whole screen
- **WHEN** the page lets the screen go
- **THEN** the frame is drawn where it was, and the folded rails' controls are back
