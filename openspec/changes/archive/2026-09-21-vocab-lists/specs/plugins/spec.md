As someone learning words,\
I want my lists kept as the vocab field's own files,\
so that a drill reads them and a search never has to.

## MODIFIED Requirements

### Requirement: A vocabulary field is brought by a plugin

A plugin SHALL bring cora a `vocab` field carrying instructions and nothing else. The
field SHALL hold vocabulary lists as its own files rather than as its documents, so
nothing indexes, searches or cites them. The field SHALL be offered and worked in
exactly as a field with no page is, and SHALL go on holding ordinary documents beside
its lists.

#### Scenario: The field is offered

- **GIVEN** the vocab plugin loaded
- **WHEN** the reader asks what fields there are
- **THEN** vocab is among them

#### Scenario: What it registers

- **GIVEN** the vocab plugin loaded
- **WHEN** what it registered is read
- **THEN** it is instructions under the vocab field, and no tool and no page

#### Scenario: A list is not a document

- **GIVEN** a list kept as a file of the vocab field
- **WHEN** that field's documents are listed
- **THEN** the list is not among them

#### Scenario: A document is still a document

- **GIVEN** a grammar note uploaded to the vocab field
- **WHEN** the reader asks what it says
- **THEN** it is searched and cited as any document is

### Requirement: A word is answered from the list it is on

A question about a word asked in the vocab field SHALL be answered from the lists that
field holds, naming the list the word was found on. A word on none of them SHALL be said
to be on none of them, and SHALL NOT be written into one.

#### Scenario: A word that is on a list

- **GIVEN** a list in the vocab field holding that word
- **WHEN** the reader asks what it means
- **THEN** the answer comes from that list and names it

#### Scenario: A word that is on no list

- **GIVEN** a field whose lists do not hold the word asked about
- **WHEN** the reader asks what it means
- **THEN** the answer says the word is on none of the lists

## ADDED Requirements

### Requirement: A pair on a list twice is drilled once

Where one list holds the same pair more than once, the field SHALL drill it once. Two
photographs of one page overlap, and a row that arrives twice is one word to learn.

#### Scenario: An overlapping photograph

- **GIVEN** a list where one pair appears twice
- **WHEN** the words that list holds are counted
- **THEN** the pair is counted once

#### Scenario: One word on two lists

- **GIVEN** two lists that each hold the same pair
- **WHEN** the words the field holds are counted
- **THEN** the pair is counted once for each list it is on
