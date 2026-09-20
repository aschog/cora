As someone with a screenshot of what I want to ask about,\
I want its words read where I added it and corrected before they are kept,\
so that what cora holds is the text I meant and the image stays on my machine.

## ADDED Requirements

### Requirement: A photo is read in the browser it was added in

A photo added to a conversation SHALL be read into text by the page itself, and the
image SHALL NOT be sent to cora or to anywhere else. The addresses the page reaches for
the reading SHALL be named ones.

#### Scenario: A photo is added

- **GIVEN** a conversation in a field
- **WHEN** the reader adds a photo
- **THEN** its words are offered as text, and no upload of the image has been made

#### Scenario: A file that is not a photo

- **WHEN** the reader adds a document that is not an image
- **THEN** it is uploaded as it always was, with nothing read and nothing to correct

### Requirement: What was read is corrected before it is kept

The text read from a photo SHALL be put to the reader to correct, and SHALL NOT reach
the field until they save it. Saving SHALL keep it as a Markdown document of the
conversation's field, named after the image. Discarding SHALL keep nothing.

#### Scenario: A reading is corrected and saved

- **GIVEN** the text read from a photo
- **WHEN** the reader edits it and saves
- **THEN** the field holds a document of that text, named after the image

#### Scenario: A reading is discarded

- **GIVEN** the text read from a photo
- **WHEN** the reader discards it
- **THEN** the field holds no new document

### Requirement: A reading that gave nothing says which nothing it was

A photo holding no text SHALL be reported as one, and a reading that could not be run at
all SHALL be reported as that instead. Neither SHALL be reported as the other, and
neither SHALL keep anything.

#### Scenario: Nothing was in the image

- **WHEN** a photo holding no text is added
- **THEN** the reader is told nothing was read in it

#### Scenario: The reader could not be fetched

- **GIVEN** a browser that cannot reach where the reading is fetched from
- **WHEN** a photo is added
- **THEN** the reader is told the reading could not be run, and not that the image was empty
