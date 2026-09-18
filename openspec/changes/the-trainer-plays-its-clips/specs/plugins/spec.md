As someone working through a set,\
I want the clip for the exercise to play where I am looking,\
so that I can see the movement without leaving the page I am training in.

## ADDED Requirements

### Requirement: A clip plays in the frame

Opening an exercise's clip SHALL play it in the frame the plan and the camera share,
starting where the plan says it starts. It SHALL NOT take the reader out of the page.

#### Scenario: A clip is opened

- **GIVEN** an exercise whose plan names a clip and a moment to start it at
- **WHEN** the reader opens that clip
- **THEN** it plays in the frame, from that moment

#### Scenario: Nowhere else to go

- **WHEN** a clip is open
- **THEN** the frame offers no link that would leave the page
