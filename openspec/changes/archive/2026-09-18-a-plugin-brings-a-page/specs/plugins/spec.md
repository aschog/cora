As a plugin author,\
I want my plugin to bring a page of its own,\
so that my field has a surface and not only a conversation.

## ADDED Requirements

### Requirement: A plugin brings the page of one field

A plugin SHALL be able to register a directory of its own as the page of one field.
The field SHALL be named: a page belongs to a field, and there is no page for every
turn. What is registered SHALL be the directory and nothing about where it is drawn.

#### Scenario: A plugin registers a page

- **GIVEN** a plugin holding a directory of its own
- **WHEN** it registers that directory as the page of its field
- **THEN** it loads, and cora holds a page for that field

#### Scenario: A page is not something a field can be without

- **GIVEN** a plugin registering a page under no field
- **WHEN** cora starts
- **THEN** it refuses, naming that plugin

### Requirement: A page that is not there costs its own path and nothing else

Registering a page SHALL NOT be held against what is on disk, the disk being free to
change after any such check. A plugin whose page directory is absent SHALL load, and
everything else it registered SHALL work. Only the page's own path SHALL be refused.

#### Scenario: The directory is not there

- **GIVEN** a plugin registering a page directory that does not exist
- **WHEN** cora starts
- **THEN** it loads, and its tools and instructions are offered as usual

#### Scenario: One broken page is not a broken cora

- **GIVEN** that plugin loaded beside another
- **WHEN** anything is asked of cora
- **THEN** it answers, and only that page's path is refused

### Requirement: One field has one page

Two plugins SHALL NOT bring the page of one field. Cora SHALL refuse such a
composition, naming both plugins and the field, as it refuses two tools of one name.

#### Scenario: Two plugins claim one field

- **GIVEN** two loaded plugins registering a page under the same field
- **WHEN** cora composes them
- **THEN** it refuses, naming both plugins and the field

#### Scenario: Two fields, two pages

- **GIVEN** one plugin registering a page under each of two fields
- **WHEN** cora composes it
- **THEN** both are held, one page per field

## MODIFIED Requirements

### Requirement: Cora says what it loaded

The system SHALL offer one listing of every plugin it loaded, naming for each its
source, the scopes it registered under, its tools by name, whether it heads a section
of the brief, the events it subscribed to, and the page it brings. A registration
carrying no scope SHALL be flagged as system-wide, because it is a claim on every turn.
The listing SHALL be readable in a terminal and on the screen, and both SHALL say the
same thing.

#### Scenario: Each plugin is listed with what it registered

- **GIVEN** several plugins loaded from different sources
- **WHEN** the listing is read
- **THEN** each is named with its source, its scopes, its tools, its instructions and
  its events

#### Scenario: A page is listed with the field it is for

- **GIVEN** a plugin bringing the page of its field
- **WHEN** the listing is read
- **THEN** that plugin carries a page, under the field it registered it for

#### Scenario: A system-wide registration is flagged

- **GIVEN** a plugin registering one thing system-wide and the rest under a scope
- **WHEN** the listing is read
- **THEN** the system-wide one is marked as such, and the scoped ones are not

#### Scenario: The same listing is on the screen

- **GIVEN** the shell serving the page
- **WHEN** the page asks what is loaded
- **THEN** it is given what the terminal listing shows, plugin for plugin

#### Scenario: A bare cora says it is bare

- **GIVEN** a deployment that named no plugin and dropped no file
- **WHEN** the listing is read
- **THEN** it says that nothing is loaded, rather than showing nothing
