As a plugin author,\
I want a field to keep files that are not documents,\
so that the data my plugin owns stays out of the search index.

## ADDED Requirements

### Requirement: A field keeps files of its own

Cora SHALL hand a plugin a place to keep files, read and written by name, holding text.
The files SHALL belong to the field rather than to the plugin, the way its documents do,
so a plugin loaded under two fields keeps two sets and neither reads the other's. A
plugin SHALL be able to list the names a field has, read one, write one, and drop one.
Writing nothing under a name SHALL drop it. What is kept SHALL outlive the turn, the
conversation and the process.

#### Scenario: What was written is read back

- **GIVEN** a plugin that wrote text under a name in a field
- **WHEN** it reads that name in a later turn
- **THEN** the text it wrote comes back

#### Scenario: One plugin, two fields

- **GIVEN** a plugin loaded under two fields, each holding different text under one name
- **WHEN** it reads that name in each field
- **THEN** it reads that field's own

#### Scenario: The names a field has

- **GIVEN** a field holding three files
- **WHEN** its names are listed
- **THEN** all three come back, and no other field's

#### Scenario: A name nothing was written under

- **WHEN** a plugin reads a name it never wrote
- **THEN** it reads nothing, and nothing fails

#### Scenario: A name dropped

- **GIVEN** a plugin that wrote text under a name
- **WHEN** it writes nothing under that name
- **THEN** reading the name comes back with nothing, and the name is not listed

### Requirement: A file a plugin keeps is not a document

A file a plugin keeps SHALL NOT be indexed, embedded, searched or cited, and SHALL NOT
appear in the document rail. It is the plugin's own data rather than the user's reading,
and what the text means SHALL be the plugin's business rather than cora's.

#### Scenario: A search does not reach it

- **GIVEN** a plugin that wrote a file whose words match a question
- **WHEN** the field is searched for those words
- **THEN** no passage of that file comes back

#### Scenario: The rail does not list it

- **GIVEN** a field holding one document and one plugin file
- **WHEN** the documents of that field are listed
- **THEN** only the document is listed

### Requirement: A name that would leave the directory is refused

A file name SHALL be one plain name. A name carrying a separator, a parent, or an
absolute path SHALL be refused rather than followed, and nothing outside the plugin's
own directory SHALL be read, written or dropped however the name is spelled.

#### Scenario: A name climbing out

- **WHEN** a file is written under a name containing `../`
- **THEN** the write is refused and nothing outside the directory changes

#### Scenario: An absolute name

- **WHEN** a file is written under a name that is an absolute path
- **THEN** the write is refused

### Requirement: A file over the cap is refused

A write larger than the deployment's cap SHALL be refused with a reason, rather than
written. The refusal SHALL say the cap, so whoever sent it knows what would fit.

#### Scenario: Too large to keep

- **WHEN** a file larger than the cap is written
- **THEN** the write is refused, the reason names the cap, and nothing is kept

### Requirement: The screen keeps a field's files

The screen SHALL be able to list the names a field's plugin keeps, read one by name,
write one, and delete one. A write under a name that exists SHALL replace it, so what is
merged is merged by whoever writes. Deleting a name nothing was written under SHALL NOT
be an error. Only the named field's own files SHALL be reachable.

#### Scenario: The screen writes a file

- **WHEN** the screen writes text under a name in a field
- **THEN** that field's plugin reads the same text back

#### Scenario: The screen lists what is there

- **GIVEN** a field whose plugin keeps two files
- **WHEN** the screen lists that field's files
- **THEN** both names come back

#### Scenario: A write replaces

- **GIVEN** a field holding a file under a name
- **WHEN** the screen writes other text under that name
- **THEN** reading it back gives the text just written

#### Scenario: A field that keeps nothing

- **WHEN** the screen lists the files of a field whose plugin kept none
- **THEN** the listing is empty, and nothing fails

#### Scenario: The screen deletes a file

- **GIVEN** a field holding a file under a name
- **WHEN** the screen deletes that name
- **THEN** the name is no longer listed, and reading it comes back with nothing

#### Scenario: Deleting what is not there

- **WHEN** the screen deletes a name nothing was written under
- **THEN** nothing fails, and no other file is touched

#### Scenario: A delete stays inside the field

- **GIVEN** two fields each holding a file under one name
- **WHEN** the screen deletes that name in one field
- **THEN** the other field still holds its own
