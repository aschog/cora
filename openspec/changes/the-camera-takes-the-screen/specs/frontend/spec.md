As someone training,\
I want the camera to take the whole screen with the controls on it,\
so that I film myself full size and still log the set.

## ADDED Requirements

### Requirement: A page that asks for the screen has it while the rails are folded

A page SHALL be able to tell the shell it wants the screen, and to let it go. While it
wants it and both rails are folded, what is left of the folded rails SHALL NOT be drawn.
The frame SHALL then be the whole screen. With a rail open, or once the page lets go or
changes, the frame SHALL be drawn where it was. Only a page on cora's own origin SHALL be
heard.

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

#### Scenario: The page changes

- **GIVEN** a frame that is the whole screen
- **WHEN** the conversation goes back to plain chat and is fixed to that field again
- **THEN** the frame drawn again is where it was

#### Scenario: Asked from another origin

- **GIVEN** a page drawn, and both rails folded
- **WHEN** something the page embeds asks for the screen from its own origin
- **THEN** nothing moves
