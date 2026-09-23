As a deployer,\
I want cora's core to hold the turn, its stores and a field's three tools alone,\
so that everything else it knows and does arrives as a plugin I choose.

## MODIFIED Requirements

### Requirement: A plugin is handed cora's own parts

The host SHALL give a plugin what cora has: document search, its field's documents, an
index to put a document of its field into, what cora remembers, and the model. It SHALL
also give the plugin a log and settings of its own, both named for the plugin rather
than for cora.

#### Scenario: A plugin uses cora's own parts

- **GIVEN** a plugin that wants to search, to read its field, to index into it, to
  remember, or to call the model
- **WHEN** it is loaded
- **THEN** the host it was handed offers each of those

#### Scenario: What a plugin logs and reads is named for it

- **GIVEN** a loaded plugin that writes a log line and reads a setting
- **WHEN** the line is written and the setting is read
- **THEN** both are named for that plugin

#### Scenario: A plugin puts a document into its field

- **GIVEN** a plugin holding a document's text and the passages cut from it
- **WHEN** it puts them into the index in a turn of its field
- **THEN** a search of that field finds a passage, and a citation opens onto the text

#### Scenario: A passage is never offered before its text can be opened

- **GIVEN** a plugin putting a document in, and an index that fails to take it
- **WHEN** the failure is reported
- **THEN** no passage of the document is searchable

#### Scenario: Another field's index is not reached

- **GIVEN** a plugin indexing a document in a turn of one field
- **WHEN** another field is searched
- **THEN** no passage of that document comes back

### Requirement: A sub-agent reads and does not act

The system SHALL offer a delegated loop what the plugin passed in, cora's own read of
the field's files, and every system-wide tool that declares no effect, writes nothing
and asks nothing. It SHALL offer it no tool that declares an effect, none that declares
it writes, none that asks, and neither of cora's own that writes or runs a command. A
tool that changes what cora keeps SHALL declare that it writes, so a loop reading
material cora does not vouch for cannot be what asks for the writing. The loop SHALL
have no search of its own: a search is offered where a plugin registered one
system-wide.

#### Scenario: An effect is withheld from a delegated loop

- **GIVEN** a scope holding both a researcher and a tool that declares an effect
- **WHEN** the researcher runs
- **THEN** the effecting tool is not among the tools it is offered
- **AND** the plugin is told which of its tools was withheld

#### Scenario: A sub-agent cannot stop the turn to ask

- **GIVEN** a delegated loop, running
- **WHEN** the tools it may call are read
- **THEN** nothing among them stops the turn, and nothing among them writes

#### Scenario: A sub-agent may read the field and not change it

- **GIVEN** a delegated loop, running
- **WHEN** the tools it may call are read
- **THEN** cora's read is among them, and neither its write nor its command is

#### Scenario: A system-wide search is offered where one is loaded

- **GIVEN** a plugin registering a search tool system-wide, and another that delegates
- **WHEN** the delegated loop's tools are read
- **THEN** the search is among them

#### Scenario: No search is offered where none is loaded

- **GIVEN** no plugin registering a search tool
- **WHEN** a delegated loop's tools are read
- **THEN** nothing among them reaches the documents

#### Scenario: A system-wide tool that acts is withheld

- **GIVEN** a plugin registering system-wide a tool that declares an effect
- **WHEN** a delegated loop's tools are read
- **THEN** it is not among them

#### Scenario: A system-wide tool that writes is withheld

- **GIVEN** a plugin registering system-wide a tool that declares it writes
- **WHEN** a delegated loop's tools are read
- **THEN** it is not among them

#### Scenario: The rule is asserted rather than described

- **GIVEN** the tools a delegated loop is offered, whatever was passed to it
- **WHEN** a guard reads them
- **THEN** it fails if any writes, stops the turn, or declares an effect

### Requirement: A plugin cora cannot have is refused by name

The system SHALL refuse a plugin it cannot load, and the refusal SHALL name the plugin
and what is wrong with it. A module defining no `extend`, one that raises while
registering, one registering a name cora has already taken, and two plugins whose names
end alike are each refused. The names cora keeps for its own SHALL be its three tools
over the field's files, and two plugins registering one tool name SHALL be refused,
naming both. A plugin SHALL be refused the name cora registers its own contributions
under, and a file or folder whose name is not a plain identifier SHALL be refused for
that. A dropped package importing what the environment does not hold SHALL be refused,
naming the folder and what went wrong — dependencies are not installed for it. Every
refusal SHALL name the plugin as it was found — a module by its path, a file or a folder
by its own name.

#### Scenario: A module that does not register is refused

- **GIVEN** a module defining no `extend`
- **WHEN** cora starts
- **THEN** it refuses, naming that module and saying it registers nothing

#### Scenario: A module that fails while registering is refused

- **GIVEN** a module whose `extend` raises
- **WHEN** cora starts
- **THEN** it refuses, naming that module and what went wrong inside it

#### Scenario: A name cora has already taken is refused

- **GIVEN** a module registering a tool under the name cora reads a file with
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the name it may not take

#### Scenario: A name another plugin took is refused

- **GIVEN** two plugins each registering a tool of one name
- **WHEN** cora starts
- **THEN** it refuses, naming both plugins and the name they share

#### Scenario: A name cora used to keep is free

- **GIVEN** one plugin registering a tool named for searching the documents
- **WHEN** cora starts
- **THEN** it loads

#### Scenario: Two plugins that cannot be told apart are refused

- **GIVEN** two plugins whose names end alike, from either source
- **WHEN** cora starts
- **THEN** it refuses, naming both and the name they share

#### Scenario: A name cora keeps for itself is refused

- **GIVEN** a plugin whose name is the one cora registers its own contributions under
- **WHEN** cora starts
- **THEN** it refuses, naming that plugin

#### Scenario: A name that is not a name is refused

- **GIVEN** a file in the plugins folder whose stem is not a plain identifier
- **WHEN** cora starts
- **THEN** it refuses, naming that file

#### Scenario: A file that cannot be read is refused by its filename

- **GIVEN** a Python file in the plugins folder that fails to import
- **WHEN** cora starts
- **THEN** it refuses, naming that file and what went wrong in it

#### Scenario: A package that cannot be imported is refused by its folder name

- **GIVEN** a dropped package importing a module the environment does not hold
- **WHEN** cora starts
- **THEN** it refuses, naming that folder and what went wrong in it

### Requirement: A field keeps files of its own

Cora SHALL hand a plugin a place to keep files, read and written by name, holding text
or bytes. The files SHALL belong to the field rather than to the plugin, the way its
documents do, so a plugin loaded under two fields keeps two sets and neither reads the
other's. A plugin SHALL be able to list the names a field has, read one as text or as
bytes, write one, and drop one. Writing nothing under a name SHALL drop it. What is kept
SHALL outlive the turn, the conversation and the process.

#### Scenario: What was written is read back

- **GIVEN** a plugin that wrote text under a name in a field
- **WHEN** it reads that name in a later turn
- **THEN** the text it wrote comes back

#### Scenario: Bytes are kept as they were

- **GIVEN** a plugin that wrote bytes that are not text under a name
- **WHEN** it reads the name as bytes, and then as text
- **THEN** the same bytes come back, and the text read comes back with nothing

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

### Requirement: The contract has a version, and a plugin says which it wants

The system SHALL read the contract version a plugin declares before calling `extend`,
and SHALL refuse one it does not offer. The version offered SHALL be 2. The refusal
SHALL name the version the plugin asked for and the version cora offers. A plugin
declaring none SHALL be taken as asking for the version cora offers.

#### Scenario: A version cora does not offer is refused

- **GIVEN** a plugin declaring contract version 1
- **WHEN** cora starts
- **THEN** it refuses, naming that plugin, the version it wants and the version offered

#### Scenario: The refusal comes before the plugin's own code runs

- **GIVEN** a plugin declaring an unsupported version and registering a tool
- **WHEN** cora refuses it
- **THEN** nothing it would have registered was registered

#### Scenario: A plugin that declares nothing is taken at cora's version

- **GIVEN** a plugin declaring no contract version
- **WHEN** cora starts
- **THEN** it is loaded

#### Scenario: The how-to says what is public and what may move

- **WHEN** the page on writing a plugin is read
- **THEN** it names the contract version, what is public, and what may move under an
  author

## ADDED Requirements

### Requirement: The core's own tools are a field's read, write and command

Cora SHALL offer the model, in every turn whose field has not claimed its files, three
tools and no others of its own: one reads a file of the field by name, one writes a file
of the field by name, and one runs a command with the field's directory as its working
directory.
None of the three SHALL wait for approval. A name that is not one plain name, or a
command naming a path outside the field's directory, SHALL be refused rather than run.
What the read and the command return SHALL reach the model labelled untrusted. A
command's output SHALL be capped, and a command SHALL be stopped after the deployment's
time, both said to the model.

#### Scenario: A bare cora offers three tools

- **GIVEN** a cora with no plugin loaded
- **WHEN** the tools it offers are listed
- **THEN** they are the read, the write and the command, and nothing else

#### Scenario: What was written is read back

- **GIVEN** a turn in a field
- **WHEN** the model writes a file by name and reads it back
- **THEN** it reads what it wrote, and the field's files list the name

#### Scenario: A command runs in the field

- **GIVEN** a field holding one file
- **WHEN** the model lists the working directory with the command tool
- **THEN** the output names that file and no other field's

#### Scenario: A command that leaves the field is refused

- **WHEN** the model runs a command naming a parent directory or an absolute path
- **THEN** it is refused, nothing runs, and the model is told why

#### Scenario: A name that is not plain is refused

- **WHEN** the model reads or writes a name carrying a separator
- **THEN** it is refused, and nothing outside the field is touched

#### Scenario: Output is capped and time is bounded

- **GIVEN** a command that prints without end
- **WHEN** it runs
- **THEN** it is stopped after the deployment's time, and the model is told the output
  was cut and the command stopped

#### Scenario: What a file holds is untrusted

- **GIVEN** a file whose text tells the model to change its rules
- **WHEN** the model reads it
- **THEN** the text arrives behind the untrusted label a passage carries

#### Scenario: Nothing waits for approval

- **GIVEN** a turn that writes a file and runs a command
- **WHEN** the turn runs
- **THEN** it never stops for the reader, and both happened

### Requirement: A field's files may be the plugin's own rather than a workspace

A plugin SHALL be able to claim the files of a field it registers under. Cora's three
tools SHALL then be offered in no turn that reaches that field, so nothing but the
plugin's own tools reads or writes what it keeps there. Every other field SHALL be a
workspace as before. A claim SHALL name a field, one that names none being refused, and
the listing SHALL show it as the plugin's contribution to that field. The plugin and the
screen SHALL still read and write the field's files as they always did.

A field is a workspace unless it says otherwise: cora keeping a subject's data behind
the tools that give it meaning is what makes a drill that puts a word and waits possible
at all, where a model free to read the file would have the answer before it asked.

#### Scenario: A claimed field offers none of cora's three

- **GIVEN** a plugin that claimed the files of its field
- **WHEN** a turn in that field lists the tools it is offered
- **THEN** none of the read, the write or the command is among them
- **AND** the plugin's own tools are

#### Scenario: Every other field is a workspace

- **GIVEN** that plugin loaded beside one that claimed nothing
- **WHEN** a turn in the other field lists the tools it is offered
- **THEN** all three are among them

#### Scenario: A turn reaching a claimed field at all is offered none of them

- **GIVEN** a turn running in a claimed field and an unclaimed one at once
- **WHEN** it lists the tools it is offered
- **THEN** none of the three is among them

#### Scenario: A claim names a field

- **GIVEN** a plugin claiming files under no field
- **WHEN** cora starts
- **THEN** it refuses, naming that plugin

#### Scenario: The plugin still reads what it claimed

- **GIVEN** a claimed field holding a file its plugin wrote
- **WHEN** the plugin reads that name in a later turn
- **THEN** the text it wrote comes back

#### Scenario: The vocabulary field claims its lists

- **GIVEN** the vocab plugin as it is shipped
- **WHEN** its registrations are read
- **THEN** it claims the files of its field, so a drill is the only way to a word

### Requirement: A plugin hears an upload land

The system SHALL run, when the reader uploads a file into a field, the handlers
subscribed to the upload event, system-wide and that field's, in load order, with the
file's name. The file SHALL be a file of that field before they run, and that field
SHALL be the one they run in. A handler answering with a sentence SHALL refuse the
upload: the reader reads the sentence, and the file is dropped. A handler that raises
SHALL refuse it on cora's own wording. An upload no handler refused SHALL be answered as
taken, naming the file and the field.

#### Scenario: A handler reads the file it was told of

- **GIVEN** a plugin subscribed to the upload event
- **WHEN** a file is uploaded into a field
- **THEN** the handler reads the file's bytes from that field, under the name it was
  handed

#### Scenario: A refusal drops the file

- **GIVEN** a handler answering with a sentence
- **WHEN** a file is uploaded
- **THEN** the reader reads the sentence, and the field does not hold the file

#### Scenario: A handler that breaks refuses on cora's wording

- **GIVEN** a handler that raises
- **WHEN** a file is uploaded
- **THEN** the upload is refused in cora's words, and the field does not hold the file

#### Scenario: Nobody subscribed

- **GIVEN** no plugin subscribed to the upload event
- **WHEN** a file is uploaded
- **THEN** it is kept as a file of the field, and the upload is answered as taken

#### Scenario: Another field's handler does not hear it

- **GIVEN** a handler subscribed under one field
- **WHEN** a file is uploaded into another
- **THEN** it does not run

#### Scenario: The listing shows the subscription

- **GIVEN** a plugin subscribed to the upload event
- **WHEN** what cora loaded is listed
- **THEN** the handler is listed under the event's name, as any handler is

### Requirement: cora ships an ask plugin

The `ask` plugin SHALL offer, system-wide, the two tools that stop a turn to ask: one
that settles a fact between values already found, and one that asks for two or more
values nobody holds. Both SHALL be gathering tools over the card every such tool
declares, so the gate puts the card and the tool runs on the answer. The fork's options
SHALL be actions, its way out SHALL be an action too, and the option taken SHALL reach
the tool. The plugin SHALL bring the section of the brief saying when to call each.

#### Scenario: A fork is settled through the gate

- **GIVEN** the plugin loaded and a round asking which of two values was meant
- **WHEN** the reader takes one
- **THEN** the round runs on, the model is told which was taken, and the trace says
  what was asked

#### Scenario: A form is filled through the gate

- **GIVEN** the plugin loaded and a round asking for a city and a day
- **WHEN** the reader writes them and sends the card
- **THEN** the round runs on, and the model is told the values in the reader's words

#### Scenario: An ask nobody could answer is refused where it was made

- **GIVEN** a round asking for no fields
- **WHEN** the gate reads the card
- **THEN** no card stands, the round is told why, and the turn answers

#### Scenario: The engine has no step of its own for asking

- **WHEN** the walk a turn takes is read
- **THEN** the rounds go from the model to the gate to the tools, and no node asks

### Requirement: cora ships a documents plugin

The `documents` plugin SHALL index an upload of a kind it reads — plain text, Markdown
and PDF — into the field it landed in. An upload of any other kind SHALL be left as the
file it landed as, rather than refused: the file belongs to the field, and a plugin that
cannot read it has no say in whether the field may hold it. One of a kind it reads that
holds no text, or is over its size cap, or is not the format its name claims, SHALL be
refused, naming the file. It SHALL
offer, system-wide, a tool that searches the field's documents and numbers what it
found to be cited, and a section of the brief saying when to call it and how to cite.
Where a search finds nothing, the model SHALL be told nothing was uploaded and to say
so rather than fill the gap. How many passages a search returns SHALL be the plugin's
own setting.

#### Scenario: An upload is searched and cited

- **GIVEN** the plugin loaded and a Markdown file uploaded into a field
- **WHEN** a question about it is asked in that field
- **THEN** the answer rests on it and cites it, and the citation opens onto its text

#### Scenario: A kind it cannot read

- **GIVEN** the plugin loaded
- **WHEN** a file of a kind it does not read is uploaded
- **THEN** the upload is taken, the field holds the file, and no passage of it is
  searchable

#### Scenario: A kind it reads that it cannot

- **GIVEN** the plugin loaded
- **WHEN** a Markdown file holding no text is uploaded
- **THEN** the upload is refused naming the file, and the field does not hold it

#### Scenario: The same bytes twice cost nothing

- **GIVEN** a file already indexed in a field
- **WHEN** the same bytes are uploaded there again
- **THEN** nothing is added, and the field lists the document once

#### Scenario: Without the plugin

- **GIVEN** no documents plugin loaded
- **WHEN** a Markdown file is uploaded
- **THEN** it is a file of the field, no passage of it is searchable, and the model is
  offered no search

#### Scenario: The depth is the plugin's setting

- **GIVEN** the plugin's setting for how many passages a search returns
- **WHEN** a search runs
- **THEN** at most that many passages come back

#### Scenario: What is read is the plugin's dependency

- **GIVEN** the documents plugin as a distribution
- **WHEN** what it reaches outside cora is read
- **THEN** the PDF reader is its own, and the app carries none

### Requirement: cora ships a memory plugin

The `memory` plugin SHALL offer, system-wide, a tool that keeps one fact the user asked
to keep, and a section of the brief saying to call it only when asked. Every turn's
brief SHALL carry what cora remembers, as notes that are data rather than instructions,
and SHALL name a subject held at two or more values, telling the model to settle it with
the ask plugin's fork. A subject SHALL be read as the words a fact opens with before its
first figure. Where the deployment keeps no memory, the plugin SHALL register nothing
and say so in its log. Where memory cannot be read, the turn SHALL be answered without
it, and the trace SHALL say the plugin could not amend the brief.

#### Scenario: A fact asked for is kept and briefs the next conversation

- **GIVEN** the plugin loaded
- **WHEN** the user asks cora to remember something
- **THEN** the fact is in what cora remembers, and the next conversation's brief
  carries it

#### Scenario: No memory, nothing registered

- **GIVEN** a deployment keeping no memory
- **WHEN** the plugin is loaded
- **THEN** it registers nothing, and the listing says so

#### Scenario: Memory that cannot be read

- **GIVEN** a memory store that cannot be read
- **WHEN** a turn runs
- **THEN** it is answered, and its trace says the memory plugin could not amend the brief

#### Scenario: Three values for one subject are reported

- **GIVEN** cora holds "bodyweight 77 kg", "bodyweight 75 kg" and "bodyweight 85 kg"
- **WHEN** a turn's brief is built
- **THEN** it names `bodyweight` as held at 3 different values, and names the fork tool

#### Scenario: Notes that agree are not reported

- **GIVEN** cora holds "bodyweight 75 kg, from the coach notes" and "bodyweight 75 kg,
  from the intake form"
- **WHEN** a turn's brief is built
- **THEN** no conflict is reported

#### Scenario: A subject held once is not reported

- **GIVEN** cora holds one note about bodyweight and one about training days
- **WHEN** a turn's brief is built
- **THEN** no conflict is reported

#### Scenario: Without the plugin

- **GIVEN** no memory plugin loaded, and facts in the store
- **WHEN** a turn runs
- **THEN** the brief carries none of them, and the model is offered no remember tool
