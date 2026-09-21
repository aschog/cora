As someone learning words,\
I want the screenshot I just corrected kept as a named list,\
so that the list is drill data rather than another document to search.

## ADDED Requirements

### Requirement: A photo read on the page is kept as one of the field's own files

What was read from a photo SHALL be kept as a file of the field it was added in, under
a name the reader gives, and never as a document: a photographed page is data the
field's plugin works from rather than prose to be answered from. The name SHALL be
required, because a file of a field's is found by its name.

#### Scenario: Kept as a file

- **GIVEN** a photo read and corrected, and a name typed
- **WHEN** the reader keeps it
- **THEN** the field holds a file of that name carrying the corrected text

#### Scenario: Never a document

- **GIVEN** a photo read and kept
- **WHEN** that field's documents are listed
- **THEN** what was read is not among them, and the rail does not show it

#### Scenario: A reading with no name

- **GIVEN** a photo read and no name typed
- **WHEN** the reader tries to keep it
- **THEN** keeping is refused until a name is given

### Requirement: The names a field already holds are offered

Where a file is being kept, the screen SHALL offer the names that field already holds as
the reader types, so an existing list is added to rather than doubled under a near-miss
of its name.

#### Scenario: A name is completed

- **GIVEN** a field holding a file called `Grundwortschatz.md`
- **WHEN** the reader types the first letters of it
- **THEN** that name is offered

### Requirement: Choosing a name that exists opens what is there

Where the name given is one the field already holds, the screen SHALL put that file's
text into the box above what was just read, so the reader corrects and merges in one
pass and keeps the whole of it. What is kept SHALL be what the box holds.

#### Scenario: Adding to a list

- **GIVEN** a field holding a list of ten words
- **WHEN** the reader reads a second photo and names that same list
- **THEN** the box holds the ten and the new ones, and keeping it writes both

#### Scenario: The merge is corrected before it lands

- **GIVEN** a merged box the reader has edited
- **WHEN** they keep it
- **THEN** the file holds what the box held, not what either part held

#### Scenario: Kept before the merge has landed

- **GIVEN** a name typed for a file the field holds
- **WHEN** the reader keeps it while that file is still being fetched
- **THEN** what is written is the merge, never the new reading alone

### Requirement: A reading is not lost to a refused write

The screen SHALL keep what was read up until the write has landed, so a name the store
refuses, a file over its cap, or a store that cannot be reached is reported over the
corrected text rather than over an empty screen. What was corrected SHALL still be
there to name again.

#### Scenario: A refused write

- **GIVEN** a reading corrected and a name the store refuses
- **WHEN** the reader keeps it
- **THEN** the reason is reported and the corrected text is still on screen

### Requirement: The composer says what it takes

The ＋ beside the question SHALL open a menu naming what can be added, rather than the
file picker itself, so what the control does is readable before it is used.

#### Scenario: The menu opens

- **WHEN** the reader clicks ＋
- **THEN** a menu offering photos and files opens, and choosing from it opens the picker
