# documents Specification

## Purpose

What cora has been given to read: an upload becomes searchable passages, and a search
of them is what a turn answers from when the question is about the user's own material.

## Requirements

### Requirement: An upload becomes searchable passages

The system SHALL take an uploaded file, cut its text into passages, index them for
search, and say how many it added.

#### Scenario: A file is uploaded

- **WHEN** a file is uploaded
- **THEN** its passages are indexed and the count of them is returned

#### Scenario: A search finds the passage that matches

- **GIVEN** an indexed document
- **WHEN** a question is searched against it
- **THEN** the passages nearest the question come back

### Requirement: The same bytes are not indexed twice

The system SHALL recognise an upload it already holds and add nothing for it.

#### Scenario: The same file is uploaded again

- **GIVEN** a file already indexed
- **WHEN** the identical bytes are uploaded again
- **THEN** nothing is added and the count is zero

### Requirement: A document that cannot be read leaves nothing behind

The system SHALL refuse an upload it cannot read, and SHALL write neither text nor index
entries for it.

#### Scenario: An unreadable upload

- **WHEN** a file that cannot be read is uploaded
- **THEN** the upload is refused, and nothing about it is searchable afterwards

### Requirement: The text behind a passage is kept with it

The system SHALL keep the cleaned text an indexed passage was cut from, so the passage
can be opened and read rather than only named, and SHALL keep it before the passage can
be retrieved.

#### Scenario: A retrieved passage can be opened

- **GIVEN** a document that has been indexed
- **WHEN** one of its passages is retrieved
- **THEN** the text that passage was cut from can be read back

### Requirement: A turn answers from the documents when the question needs them

The system SHALL offer the model a search over the indexed documents, and SHALL let a
turn answer from what the search returned.

#### Scenario: A document question is answered from the search

- **GIVEN** an indexed document holding the answer
- **WHEN** a question about it is asked
- **THEN** the turn searches, and answers from what came back

#### Scenario: A question needing no document searches nothing

- **WHEN** a question the model can answer without the documents is asked
- **THEN** no search is made and the answer stands on its own
