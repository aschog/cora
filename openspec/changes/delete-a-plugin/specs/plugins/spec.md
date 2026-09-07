As an operator,\
I want to delete a plugin and everything under it from the page,\
so that a plugin I am finished with leaves nothing of itself behind.

## Purpose

Removing a plugin from a running cora, and taking its documents, its passages and its
conversations with it. What a shell cannot reach is the point of it.

## ADDED Requirements

### Requirement: A plugin is deleted with everything under it

The system SHALL delete, on one request naming a loaded plugin: its entry in the
plugins folder, the documents and the passages of every field it registered, and every
conversation pinned to one of those fields. An entry SHALL go whatever shape it has — a
file, a package folder, or a symlink. A symlink SHALL be unlinked rather than followed,
so what it points at is left where it is. The entry SHALL go last, so a delete that
failed part way can be asked for again.

#### Scenario: A dropped package goes

- **GIVEN** a plugin loaded from a package folder in the plugins folder
- **WHEN** it is deleted
- **THEN** the folder is gone, and the next request serves without the plugin

#### Scenario: A symlinked plugin leaves its target alone

- **GIVEN** a plugin loaded through a symlink into a repository
- **WHEN** it is deleted
- **THEN** the symlink is gone and what it pointed at is untouched

#### Scenario: Its documents and passages go

- **GIVEN** a plugin registering `travel`, and documents uploaded into that field
- **WHEN** the plugin is deleted
- **THEN** neither the files nor their passages are there to be listed or searched

#### Scenario: Its conversations go, both halves

- **GIVEN** a conversation pinned to a field only this plugin brings
- **WHEN** the plugin is deleted
- **THEN** the conversation is listed nowhere, and its thread holds no pin and nothing kept

#### Scenario: A plugin registering two fields takes both

- **GIVEN** a plugin registering under two fields, each holding documents
- **WHEN** the plugin is deleted
- **THEN** the documents of both fields go

#### Scenario: A plugin with no field of its own goes by its entry alone

- **GIVEN** a plugin registering nothing under a field, screening every turn
- **WHEN** it is deleted
- **THEN** its entry is gone, and it has nothing else to take with it

#### Scenario: A half that failed leaves the plugin deletable

- **GIVEN** a delete whose documents could not be dropped
- **WHEN** the plugin listing is read again
- **THEN** the plugin is still listed, and deleting it again is what was asked for

### Requirement: A deleted plugin takes nothing that is not its own

The system SHALL leave what cora remembers about the user, and what an approved effect
wrote outside cora's stores. Every other plugin, its fields and its documents SHALL be
left. A conversation pinned to no field SHALL be left, whatever it was answered about.

#### Scenario: Memory and output are left

- **GIVEN** facts cora remembers, and a file an approved effect wrote
- **WHEN** a plugin is deleted
- **THEN** both are still there

#### Scenario: Another field is left alone

- **GIVEN** two plugins, each with documents in its own field
- **WHEN** one is deleted
- **THEN** the other's documents and conversations are untouched

#### Scenario: An unpinned conversation is left

- **GIVEN** a conversation holding no pin, answered while the plugin was loaded
- **WHEN** the plugin is deleted
- **THEN** the conversation is still listed and still readable

### Requirement: A delete names a loaded plugin, and nothing else

The system SHALL delete only a plugin it has loaded from the plugins folder, named as
that plugin is named. A name nothing loaded SHALL be refused. A plugin named in the
environment SHALL be refused, having no entry to delete and returning at the next
start. Nothing a request carries SHALL be read as a path.

#### Scenario: A name nothing loaded is refused

- **GIVEN** a deployment loading `travel`
- **WHEN** a delete names `voyage`
- **THEN** it is refused, and nothing is deleted

#### Scenario: A plugin named in the environment is refused

- **GIVEN** a plugin named in `CORA_PLUGINS`
- **WHEN** a delete names it
- **THEN** it is refused, saying it is fixed at start, and nothing is deleted

#### Scenario: A name that is a path is refused

- **GIVEN** a delete naming a path rather than a plugin
- **WHEN** it arrives
- **THEN** it is refused, and nothing outside the plugins folder is touched

### Requirement: Deleting a plugin is asked about first

The page SHALL offer the control only on a field a deleteable plugin brings, and SHALL
ask before deleting. The question SHALL name the plugin, every field going with it, and
what is not lost. After the delete the page SHALL read the fields, the documents and the
conversations again, rather than keep its own account of what changed.

#### Scenario: The control is on the field the plugin brings

- **GIVEN** a field brought by a plugin in the plugins folder
- **WHEN** the fields are listed
- **THEN** that field carries a delete control

#### Scenario: A field with nothing to delete carries no control

- **GIVEN** a field the configuration names, with no plugin behind it
- **WHEN** the fields are listed
- **THEN** it carries no delete control

#### Scenario: The question says what is lost and what is not

- **GIVEN** a reader using the control
- **WHEN** the question is shown
- **THEN** it names the plugin and its fields, and says memory and saved files stay

#### Scenario: Nothing goes until the reader confirms

- **GIVEN** the question shown
- **WHEN** the reader leaves it
- **THEN** the plugin, its documents and its conversations are all still there
