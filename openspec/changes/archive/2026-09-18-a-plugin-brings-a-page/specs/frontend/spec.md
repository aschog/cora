As a reader,\
I want a plugin's page served by the cora I am already running,\
so that it reaches my documents and my conversations without a second process.

## ADDED Requirements

### Requirement: A field's page is served beside cora's own

The system SHALL serve a registered page from the process that serves cora's page and
its API, under a path naming the field. The path it reports for a field SHALL be the
one that answers, and SHALL answer with the directory's entry page. Every file under
the directory SHALL be reachable, and nothing outside it SHALL be, whatever a request
spells.

#### Scenario: The page is asked for

- **GIVEN** a loaded plugin bringing the page of a field
- **WHEN** the path reported for that field is asked for
- **THEN** the entry page of its directory is answered

#### Scenario: A file beside the entry page

- **GIVEN** the same page, whose directory holds a script and an image
- **WHEN** either is asked for under that path
- **THEN** it is answered as what it is

#### Scenario: A request climbing out of the directory

- **GIVEN** a request under that path spelling its way above the directory
- **WHEN** it is answered
- **THEN** it is refused, and no file outside the directory is served

#### Scenario: A link inside the directory pointing out of it

- **GIVEN** a page directory holding a symlink to a file above it
- **WHEN** that link is asked for
- **THEN** it is refused, and what it points at is not served

#### Scenario: A field with no page

- **GIVEN** a loaded plugin registering a field and no page
- **WHEN** that field's path is asked for
- **THEN** the request is refused, and cora's own page still answers

#### Scenario: A page whose directory is gone

- **GIVEN** a loaded plugin whose page directory has since been removed
- **WHEN** that field's path is asked for
- **THEN** the request is refused, and cora answers everything else as usual

### Requirement: A page is served as it stands on disk

The system SHALL answer with the file as it is at the moment of the request, and SHALL
ask the browser to check back rather than reuse what it holds. A file that has not
changed SHALL be answerable without being sent again.

#### Scenario: A page file is edited

- **GIVEN** a served page whose file is then changed on disk
- **WHEN** it is asked for again
- **THEN** the answer is the file as it now stands

#### Scenario: The browser is told to check back

- **GIVEN** any file served from a page directory
- **WHEN** the answer is read
- **THEN** it says it must be revalidated before being reused

### Requirement: A page is served while its plugin is loaded, and no longer

The system SHALL serve a page as soon as the plugin bringing it is loaded, and SHALL
stop when that plugin is gone. Neither SHALL need a restart, the plugins folder being
live.

#### Scenario: A plugin is dropped

- **GIVEN** a running cora, and a plugin bringing a page dropped into the folder
- **WHEN** its field's path is asked for
- **THEN** its page is answered, with nothing restarted

#### Scenario: A plugin is deleted

- **GIVEN** that plugin deleted from the folder
- **WHEN** its field's path is asked for again
- **THEN** the request is refused, and cora's own page still answers

### Requirement: The page says which fields have a page

The system SHALL say, with the fields it offers, which of them has a page and where it
is served. A field no plugin brought a page for SHALL be named without one.

#### Scenario: A field with a page

- **GIVEN** a loaded plugin bringing the page of its field
- **WHEN** the fields on offer are asked for
- **THEN** that field is named with the path its page is served under

#### Scenario: A field without one

- **GIVEN** a loaded plugin registering tools and no page
- **WHEN** the fields on offer are asked for
- **THEN** its field is named, and no page is claimed for it
