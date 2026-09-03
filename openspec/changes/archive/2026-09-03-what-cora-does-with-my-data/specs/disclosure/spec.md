As a person uploading my own documents and loading someone else's plugin,\
I want one page saying what leaves my machine, what is stored, what the model is told and
what a plugin may do,\
so that I can judge both costs before I take either.

## Purpose

What cora is obliged to say about itself: where a reader's data goes, what the
safeguards do and do not catch, and what loading someone else's plugin costs in trust.

## ADDED Requirements

### Requirement: One page says where a reader's data goes

The docs SHALL carry a privacy and ethics page. It SHALL name every host cora contacts,
distinguishing those a reader's data reaches — the model provider, and any service a
loaded plugin calls — from those cora only fetches from. It SHALL name every place cora
keeps something: the vector index, the stored document text, remembered facts, the
recorded conversations and their checkpoints, the debug log, and the output directory,
with the setting that moves each. It SHALL say which work happens locally.

#### Scenario: A reader looks for what leaves the machine

- **WHEN** a reader opens the privacy and ethics page
- **THEN** it names the model provider as the destination every turn's prompt reaches
- **AND** it names the live service the travel scope calls
- **AND** it names the host the embedding model is fetched from, and says that call sends
  nothing of the reader's
- **AND** it says that embedding then runs locally, so no document text is sent to be
  indexed

#### Scenario: A reader looks for what is kept

- **WHEN** they read the same page
- **THEN** it names each store, what it holds, and the setting that moves it
- **AND** it says that everything cora keeps is a file on their own machine

### Requirement: The page says what the model is told

The page SHALL say what reaches the model on a turn: cora's own brief, the plugin
instructions loaded for that field, the remembered facts, the conversation within its
history window, and the results of the tools the turn called.

#### Scenario: A reader asks what the model sees

- **WHEN** they read the page
- **THEN** it says that retrieved passages and remembered facts reach the model
- **AND** it says that a question refused on the way in never reaches it

### Requirement: The page says what the safeguards do not catch

The page SHALL state the limits of each safeguard rather than implying it is complete.
It SHALL say that the injection screen is a plugin, absent unless the deployment names
it, so a cora started without it screens nothing at all. It SHALL say that the screen,
where it is loaded, reads the reader's question only, that it does not scan uploaded text
or what a tool returned, and that rewording gets past it. It SHALL say which of its log
lines are truncated and which are not. It SHALL say
that the untrusted-data label marks retrieved and fetched material for the model and no
plugin can remove it, while the model may still be led by what it reads. It SHALL name
where an answer can be wrong.

#### Scenario: A reader asks what the injection screen misses

- **WHEN** they read the page
- **THEN** it says the screen reads the question and not the documents
- **AND** it says a deployment that did not load the plugin has no screen
- **AND** it does not claim the screen makes prompt injection impossible

#### Scenario: A reader asks where an answer can be wrong

- **WHEN** they read the page
- **THEN** it names retrieval missing a passage, a document being out of date, and the
  model misreading what it was given

### Requirement: The page says what loading a plugin costs in trust

The page SHALL say that a loaded plugin is arbitrary code running with the reader's own
permissions — instructions the model follows, tools it may call, handlers that can refuse
or amend, and effects outside cora — and that this is true of every harness of this kind.
It SHALL separate what cora enforces whatever a plugin does from what it does not.

#### Scenario: A reader decides whether to load someone else's plugin

- **WHEN** they read the page
- **THEN** it says a plugin runs with their own permissions, and names the four things it
  may contribute
- **AND** it names what the contract hands a plugin — the documents, what cora remembers
  including deleting it, and the model — and that none of that waits for approval, because
  the gate covers what changes outside cora

#### Scenario: A reader asks what holds regardless of the plugin

- **WHEN** they read the page
- **THEN** it names the approval gate before an effect, the untrusted label on retrieved
  and fetched text, the output confined to the configured directory, and the tool names a
  plugin may not take
- **AND** it names what cora does not enforce: no sandbox, no network restriction, and no
  review of what a plugin's instructions tell the model

### Requirement: The page's claims match what cora does

Every claim the page makes SHALL be true of the code at the commit it ships in, and a
safeguard SHALL be described as it behaves rather than as it was intended to behave. The
page's list of what cora keeps SHALL be held against the settings themselves, discovered
rather than listed, so a store that moves, a store that is added, or a renamed setting is
caught. Every other claim is held by a person reading it, as this project's rules require
of prose.

#### Scenario: A store the page names has moved

- **GIVEN** the page lists the locations cora keeps something in, and the setting for each
- **WHEN** one of those settings is changed, or another store is added
- **THEN** a guard fails until the page names it and its setting

#### Scenario: A safeguard grows or shrinks

- **GIVEN** the page says what the injection screen catches
- **WHEN** the screen's rules change
- **THEN** nothing fails automatically, and the page is corrected in review — which is
  the cost of prose, and is stated here rather than left to be discovered
