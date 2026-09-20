As someone learning a language,\
I want a screenshot of a vocabulary list read and corrected into cora's documents,\
so that the words I am learning sit in a field cora can answer from.

## ADDED Requirements

### Requirement: A vocabulary field is brought by a plugin

A plugin SHALL bring cora a `vocab` field carrying instructions and a page of its own,
and no tools. The field SHALL hold vocabulary lists as documents, and the plugin SHALL
answer about them from what that field holds rather than from what it knows.

#### Scenario: The field is offered

- **GIVEN** the vocab plugin loaded
- **WHEN** the reader asks what fields have a page
- **THEN** vocab is named with the path its page is served under

#### Scenario: What it registers

- **GIVEN** the vocab plugin loaded
- **WHEN** what it registered is read
- **THEN** it is instructions and a page under the vocab field, and no tool

### Requirement: A screenshot is read where it is dropped

The page SHALL read a dropped or pasted screenshot into rows of two words, and the image
SHALL NOT leave the reader's browser. A reading that finds nothing SHALL say so and
leave the reader an empty list to type into. The addresses the page reaches SHALL be
cora's own for the save, and named hosts for the reading itself.

#### Scenario: A screenshot is dropped

- **GIVEN** the page drawn
- **WHEN** a screenshot of a word list is dropped on it
- **THEN** the words are offered as rows, a German word beside the word being learnt

#### Scenario: Nothing could be read

- **WHEN** an image holding no text is dropped
- **THEN** the page says it read nothing, and offers a list to type into

#### Scenario: Where it reaches

- **WHEN** the addresses in the page are read
- **THEN** the only one it posts to is cora's own, and every other host is one the
  plugin's own suite names

### Requirement: Nothing is saved until the reader has corrected it

The rows SHALL be editable and removable, and the page SHALL save nothing until the
reader saves. What the document carries SHALL be what the rows say when they are saved,
so a reading the reader corrected is corrected everywhere.

#### Scenario: A misread word is corrected

- **GIVEN** rows offered from a screenshot
- **WHEN** the reader edits a word and saves
- **THEN** the document holds the edited word, and not what was read

#### Scenario: Left without saving

- **GIVEN** rows offered from a screenshot
- **WHEN** the reader leaves without saving
- **THEN** the vocab field holds no new document

### Requirement: A saved list is one document of the vocab field

Saving SHALL upload one Markdown document into the vocab field. Its heading SHALL name
the language and what the list is called, and its body SHALL be a table of two columns,
German beside the language being learnt. A list with no row SHALL NOT be saved, and a
save cora refuses SHALL be reported with the rows left where the reader can copy them.

#### Scenario: A list is saved

- **GIVEN** rows the reader has corrected, under a named language
- **WHEN** the reader saves them
- **THEN** a document in the vocab field holds that heading and those pairs

#### Scenario: Two languages

- **GIVEN** a list saved for one language
- **WHEN** a list for another language is saved
- **THEN** the field holds two documents, each named by its own language

#### Scenario: Nothing to save

- **WHEN** the reader saves a list holding no row
- **THEN** nothing is uploaded

#### Scenario: A save cora refuses

- **GIVEN** rows the reader has corrected
- **WHEN** the upload is refused
- **THEN** the page says so, and the rows are still there to copy

### Requirement: What was saved is what cora answers from

A list uploaded by the page SHALL be searched and cited as any other document of that
field is, so a question about a word is answered from the list it came from.

#### Scenario: A word is asked about

- **GIVEN** a list saved in the vocab field
- **WHEN** the reader asks what one of its words means
- **THEN** the answer comes from that list and cites it
