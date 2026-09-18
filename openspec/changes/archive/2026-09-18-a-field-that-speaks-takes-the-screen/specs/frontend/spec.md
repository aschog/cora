As a lifter,\
I want the trainer on my screen the moment I start training on my watch,\
so that the workout I am logging into is not something I have to go and find.

## ADDED Requirements

### Requirement: A field that speaks takes the screen

The shell SHALL ask each field that has a page for its notice, every few seconds. A
notice written after the last one that field was seen to hold SHALL open that field's
newest conversation, whatever the notice says — the shell reads that one was written and
nothing of what is in it. A field with no conversation pinned to it SHALL open nothing,
and neither SHALL a notice already standing when the page was loaded.

#### Scenario: A notice is written while the reader is elsewhere

- **GIVEN** a conversation pinned to a field with a page, and another conversation on
  the screen
- **WHEN** that field's notice is written
- **THEN** the pinned conversation is opened, and its field's page is what the screen is
  about

#### Scenario: The newest of several

- **GIVEN** two conversations pinned to that field
- **WHEN** its notice is written
- **THEN** the one that answered most recently is opened

#### Scenario: Already there

- **GIVEN** that field's conversation already on the screen
- **WHEN** its notice is written
- **THEN** the screen does not move

#### Scenario: A field nothing is pinned to

- **GIVEN** a field with a page and no conversation pinned to it
- **WHEN** its notice is written
- **THEN** nothing is opened and the reader is left where they were

#### Scenario: What was already standing

- **GIVEN** a field whose notice was written before the page was loaded
- **WHEN** the page loads
- **THEN** the screen stays on the conversation the address names

#### Scenario: A field with no page

- **GIVEN** a field that brought no page
- **WHEN** the shell asks for the notices
- **THEN** that field is not among them

#### Scenario: Nothing answering

- **GIVEN** a notice that cannot be read
- **WHEN** the shell asks for it
- **THEN** the rest of the page is unaffected and no banner is raised
