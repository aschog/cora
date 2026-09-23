## MODIFIED Requirements

### Requirement: A photo read on the page is kept as one of the field's own files

What was read from a photo SHALL be kept as a file of the field it was added in, under a
name the reader gives. The screen holding the reading SHALL offer one box asking whether
to make it a document too. Unticked, it is a file and never a document: a photographed
page is data the field's plugin works from rather than prose to be answered from.
Ticked, it is uploaded as a document of that field under that name, and indexed as any
upload is. The name SHALL be required, because a file of a field's is found by its name.

#### Scenario: Kept as a file

- **GIVEN** a photo read and corrected, and a name typed
- **WHEN** the reader keeps it
- **THEN** the field holds a file of that name carrying the corrected text

#### Scenario: Never a document

- **GIVEN** a photo read and kept with the box unticked
- **WHEN** that field's documents are listed
- **THEN** what was read is not among them, and the rail does not show it

#### Scenario: Asked to be a document

- **GIVEN** a photo read and kept with the box ticked
- **WHEN** that field's documents are listed
- **THEN** what was read is among them under the name given, and a search of the field
  reaches its text

#### Scenario: A reading with no name

- **GIVEN** a photo read and no name typed
- **WHEN** the reader tries to keep it
- **THEN** keeping is refused until a name is given
