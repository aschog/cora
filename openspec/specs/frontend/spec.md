# frontend Specification

## Purpose

What cora is used through: a page and a chat, each over the same assembled app, and
each started by a documented command of its own.

## Requirements

### Requirement: Every frontend cora ships is one that is run

The system SHALL serve its page and its API from one process. Every frontend the
workspace ships SHALL run over the same assembled app, and SHALL be started by a
documented command of its own. The system SHALL hold no frontend nobody runs — code in
the tree that no command starts is removed rather than kept as a choice.

#### Scenario: The page is served beside the API

- **WHEN** the shell is asked for the page and for the API
- **THEN** one process answers both

#### Scenario: Every frontend shipped is one a command starts

- **WHEN** the frontends the workspace ships are listed
- **THEN** each of them is named by a documented command that starts it

#### Scenario: No code reaches for a framework its own portion was not given

- **WHEN** the shipped code is read
- **THEN** nothing imports a framework the frontend it sits in did not declare, and the
  check names any file that does

### Requirement: A part of the page that cannot be drawn is replaced by a sentence

Where a column or a panel throws while rendering, the page SHALL draw a sentence in its
place. The sentence SHALL name what could not be drawn, and SHALL replace nothing else.

#### Scenario: A panel that throws says so

- **GIVEN** a store answering with a shape the sessions panel cannot read
- **WHEN** the reader opens that panel
- **THEN** they are told that panel could not be drawn

#### Scenario: What threw is on the console

- **GIVEN** a part of the page that throws while rendering
- **WHEN** it is caught
- **THEN** the throw and the tree it came from reach the console

### Requirement: The rest of the page is still drawn

A column that could not be drawn SHALL NOT unmount the others. The conversation, the
rails and the controls outside that column remain usable.

#### Scenario: The conversation survives a broken panel

- **GIVEN** a panel that threw while being drawn
- **WHEN** the reader looks at the page
- **THEN** the conversation and the documents rail are still there

### Requirement: A panel that broke is left behind by moving to another

The strip that chooses between panels SHALL stay outside what it chooses. Moving to
another panel SHALL draw that panel rather than the sentence.

#### Scenario: Switching tabs escapes it

- **GIVEN** a panel that threw while being drawn
- **WHEN** the reader chooses another panel
- **THEN** that panel is drawn, and the sentence is gone

### Requirement: Trying again re-draws what threw

The sentence SHALL offer to draw the part again. Taking it SHALL re-draw the children
rather than reload the page.

#### Scenario: What was mended is drawn

- **GIVEN** a part of the page that threw, and has since been given something it can draw
- **WHEN** the reader tries again
- **THEN** it is drawn

#### Scenario: What still throws says so again

- **GIVEN** a part of the page that throws, and still would
- **WHEN** the reader tries again
- **THEN** they are told again that it could not be drawn

### Requirement: cora answers in a Telegram chat

The system SHALL answer a message sent to its bot, running the turn over the same app
the page runs it over. The answer SHALL arrive in the chat it was asked in, and SHALL
name the documents it rests on where it rests on any.

#### Scenario: A question is answered in the chat

- **GIVEN** a bot running against an app whose documents are indexed
- **WHEN** an allowed chat sends a question
- **THEN** the answer is sent back to that chat

#### Scenario: An answer names what it rests on

- **GIVEN** a question answered from an indexed document
- **WHEN** the answer arrives
- **THEN** the documents it cites are named under it

### Requirement: A chat is a conversation

The system SHALL run every turn of one chat on one thread, so what was said before is
carried into what is asked next. Two chats SHALL NOT share a thread.

#### Scenario: The second question knows the first

- **GIVEN** a chat that has already been answered once
- **WHEN** it asks a question that refers back to that answer
- **THEN** the turn runs on the same thread, and the earlier turn is in its history

#### Scenario: Two chats do not read each other

- **GIVEN** two allowed chats that have each asked something
- **WHEN** either asks again
- **THEN** its turn carries only what that chat said

### Requirement: A turn that stops to ask, asks in the chat

Where a turn pauses on a card, the system SHALL send the card's prompt to the chat with
its ways off numbered, and with the values the card already holds above them. A reply naming one of
those numbers SHALL finish the turn on that action. Any other reply SHALL be told what the open card expects, and SHALL leave the
turn parked. The values the card carries SHALL travel back as they came, and an action
held closed until a value is written SHALL NOT be offered.

#### Scenario: The card is put as numbered choices

- **GIVEN** a turn that pauses on a card offering two ways off
- **WHEN** the pause reaches the chat
- **THEN** the prompt is sent with both ways off numbered

#### Scenario: What would be approved is shown before the yes

- **GIVEN** a turn paused on a card put up to approve an effect
- **WHEN** the card reaches the chat
- **THEN** the values that effect would run on are above the numbered ways off

#### Scenario: A number finishes the turn

- **GIVEN** a chat holding an open card
- **WHEN** it replies with the number of one way off
- **THEN** the turn finishes on that action, and its answer arrives

#### Scenario: Anything else leaves the card open

- **GIVEN** a chat holding an open card
- **WHEN** it replies with something that names no way off
- **THEN** it is told what the card expects, and the turn is still parked

#### Scenario: A way off that needs a value written is not offered

- **GIVEN** a card whose action waits on a value the chat cannot write
- **WHEN** the card is put to the chat
- **THEN** that action is not among the numbered ways off

### Requirement: Only the chats named are answered

The system SHALL answer only the chats its deployment names, and SHALL send nothing at
all to any other. A message from a chat it does not answer SHALL be recorded as the id it
came from and as nothing that was said, because that id is the one an operator has no
other way to learn. A deployment that names no chat, or holds no bot token, SHALL refuse
to start and SHALL say which of the two is missing.

#### Scenario: A chat nobody named is not answered

- **GIVEN** a bot naming one chat
- **WHEN** a message arrives from another
- **THEN** no reply is sent, and no turn is run

#### Scenario: A chat nobody named is recorded by its id and by nothing else

- **GIVEN** a bot naming one chat
- **WHEN** a message arrives from another
- **THEN** that chat's id is recorded, and no word of the message is

#### Scenario: A bot allow-listing nobody refuses to start

- **GIVEN** a deployment holding a bot token and naming no chat
- **WHEN** the bot is started
- **THEN** it refuses, saying no chat is allowed

#### Scenario: A bot with no token refuses to start

- **GIVEN** a deployment naming a chat and holding no bot token
- **WHEN** the bot is started
- **THEN** it refuses, saying the token is missing

### Requirement: A turn that fails says so in the chat

Where a turn fails, the system SHALL send the chat a sentence saying so, and SHALL leave
the bot answering. A failure cora modelled SHALL be reported in its own words, and one it
did not SHALL be reported as one sentence with nothing of the failure in it.

#### Scenario: A refused question is reported in cora's words

- **GIVEN** a chat whose question a rule refuses
- **WHEN** the turn is run
- **THEN** the chat is sent what the refusal says

#### Scenario: A failure nobody modelled is one sentence

- **GIVEN** a turn that fails in a way cora does not model
- **WHEN** it fails
- **THEN** the chat is sent one sentence, carrying nothing of the failure

#### Scenario: The bot keeps answering after a failure

- **GIVEN** a chat whose turn has just failed
- **WHEN** it asks something else
- **THEN** that question is answered

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

### Requirement: A fixed field's page is what the screen is about

Where the conversation is fixed to a field that has a page, the page SHALL fill the
middle of the screen and the conversation SHALL move into the rail beside it. Where it
is fixed to a field with no page, or fixed to nothing, the screen SHALL be as it was.

#### Scenario: A field with a page is fixed to

- **GIVEN** a loaded plugin bringing the page of a field
- **WHEN** the reader fixes the conversation to that field
- **THEN** the page is drawn in the middle, and the conversation is in the rail

#### Scenario: One field is the field it is fixed to

- **GIVEN** a deployment offering one field, whose plugin brought a page
- **WHEN** the reader opens cora, having pinned nothing
- **THEN** the page is drawn, there being no other field the conversation could be in

#### Scenario: A field with no page

- **GIVEN** a loaded plugin registering a field and no page
- **WHEN** the reader fixes the conversation to it
- **THEN** the conversation is in the middle, as it is with nothing fixed

#### Scenario: Nothing is fixed to

- **GIVEN** a conversation answered in a field whose plugin brought a page
- **WHEN** the reader has fixed it to nothing
- **THEN** the conversation is in the middle, the page being what a fixed field brings

#### Scenario: The plugin goes while it is being read

- **GIVEN** a page drawn for a fixed field
- **WHEN** the plugin bringing it is deleted
- **THEN** the conversation returns to the middle without the reader reloading

### Requirement: The conversation is reachable whatever the rail is showing

Where a conversation fixed to a field with a page is open, the sessions panel SHALL be
that conversation's chat, filling the rail. It SHALL offer a way back to the list of
conversations, and opening one from that list SHALL make the rail its chat. A turn asked
there SHALL NOT move the panels to the steps, which would take the chat off the screen.

#### Scenario: Asking does not take the conversation away

- **GIVEN** a page drawn, and the rail showing its conversation
- **WHEN** the reader asks something
- **THEN** the conversation is still shown, with what they typed and what came back

#### Scenario: Back to the others

- **GIVEN** the rail showing a conversation
- **WHEN** the reader takes the way back
- **THEN** the list of conversations is shown in its place

#### Scenario: Into another one

- **GIVEN** the list of conversations shown
- **WHEN** the reader opens one that is fixed to a field with a page
- **THEN** the rail is that conversation's chat

#### Scenario: Moving between panels

- **GIVEN** the rail showing a conversation
- **WHEN** the reader chooses another panel
- **THEN** that panel is drawn in its place, and the conversation is the one tab back

#### Scenario: A panel that cannot be drawn

- **GIVEN** a panel that throws while being drawn
- **WHEN** the reader looks at the rail
- **THEN** they are told that panel could not be drawn, and the page is still there

### Requirement: The conversation in the rail says which one it is

Drawn in the rail, under a list its own row is in, the conversation SHALL be headed by
the question that opened it, so the reader can tell it from the ones listed above.

#### Scenario: The open conversation is named

- **GIVEN** a page drawn, and a conversation that has been answered once
- **WHEN** the reader looks at the rail
- **THEN** the conversation is headed by the question it was opened with

#### Scenario: A conversation that has said nothing

- **GIVEN** a page drawn, and a conversation nothing has been asked in
- **WHEN** the reader looks at the rail
- **THEN** it is headed as the new one it is, and named by no question

### Requirement: The page can have the whole width

Folding the rail beside a page SHALL give the page the width the rail held. Unfolding it
SHALL bring the conversation back, with what was said still there.

#### Scenario: Folding for width

- **GIVEN** a page drawn with the conversation beside it
- **WHEN** the reader folds that rail
- **THEN** the page is drawn across the width, and the control that unfolds it remains

#### Scenario: Coming back to the conversation

- **WHEN** the reader unfolds the rail again
- **THEN** the conversation is drawn as they left it

### Requirement: A page that asks for the screen has it while the rails are folded

A page SHALL be able to tell the shell it wants the screen, and to let it go. While it
wants it and both rails are folded, what is left of the folded rails SHALL NOT be drawn.
The frame SHALL then be the whole screen. With a rail open, or once the page lets go or
changes, the frame SHALL be drawn where it was. The reader SHALL be able to take the
screen back without the page, since no control of the shell's is reachable while it is
given. Only a page on cora's own origin SHALL be heard.

#### Scenario: Asked with both rails folded

- **GIVEN** a page drawn, and both rails folded
- **WHEN** the page asks for the screen
- **THEN** the frame is the whole screen

#### Scenario: Asked with a rail open

- **GIVEN** a page drawn beside an open rail
- **WHEN** the page asks for the screen
- **THEN** the frame is drawn where it was, and folding both rails then gives it the screen

#### Scenario: Let go

- **GIVEN** a frame that is the whole screen
- **WHEN** the page lets the screen go
- **THEN** the frame is drawn where it was, and the folded rails' controls are back

#### Scenario: Taken back

- **GIVEN** a frame that is the whole screen
- **WHEN** the reader presses Escape, wherever they are typing
- **THEN** the frame is drawn where it was, whatever the page does

#### Scenario: The page changes

- **GIVEN** a frame that is the whole screen
- **WHEN** the conversation goes back to plain chat and is fixed to that field again
- **THEN** the frame drawn again is where it was

#### Scenario: Asked from another origin

- **GIVEN** a page drawn, and both rails folded
- **WHEN** something the page embeds asks for the screen from its own origin
- **THEN** nothing moves

### Requirement: A page is framed as the plugin's own

A page SHALL be framed so that it may use the camera, and SHALL NOT be framed as though
cora contained it — its reach being the trust the reader extended by loading the plugin.
The frame SHALL be named for the field it belongs to.

#### Scenario: The frame is named

- **GIVEN** a page drawn for a field
- **WHEN** the screen is read by name
- **THEN** the frame is named for that field

#### Scenario: A page asking for the camera

- **GIVEN** a page whose script asks for the camera
- **WHEN** it asks
- **THEN** the frame does not refuse it on cora's behalf

### Requirement: A conversation chatted in the rail says which one it is

The chat SHALL be headed by the question that opened the conversation, which is what the
list beside it calls that conversation too.

#### Scenario: The head of an answered conversation

- **GIVEN** a conversation of two turns fixed to a field with a page
- **WHEN** it is chatted in the rail
- **THEN** its head carries the question it was opened with

#### Scenario: A conversation that has said nothing

- **GIVEN** a conversation nothing has been asked in
- **WHEN** it is chatted in the rail
- **THEN** its head says it is a new one

### Requirement: A conversation that belongs to a field with a page is marked in the list

Every conversation in the list that is fixed to a field bringing a page SHALL carry a
mark the others do not, and the list SHALL say what the mark means.

#### Scenario: Marked and unmarked together

- **GIVEN** conversations fixed to a field with a page, and others fixed to nothing
- **WHEN** the list is read
- **THEN** the first carry the mark and the rest do not

#### Scenario: What the mark means

- **WHEN** the list holds a marked conversation
- **THEN** it says that such a conversation opens as a chat in this rail

### Requirement: A conversation beside its field's page does not name the field

Where a conversation is chatted beside the page of the field it is fixed to, the strip
naming that field SHALL NOT be drawn: the page is the field, in front of the reader, and
the strip is a label under a control they can no longer use. Where nothing else stands
for the field, that strip SHALL be drawn as it always was.

#### Scenario: Beside a page

- **GIVEN** a conversation chatted in the rail beside its field's page
- **WHEN** the reader looks at the rail
- **THEN** the field is not named there

#### Scenario: In the middle

- **GIVEN** a conversation fixed to a field with no page
- **WHEN** the reader looks at it
- **THEN** the strip names the field, nothing else there doing so

### Requirement: A conversation fixed to no page is drawn where it always was

A conversation fixed to a field with no page, or fixed to nothing, SHALL be drawn in the
middle of the screen, and the sessions panel SHALL be the list alone.

#### Scenario: Opening one that has no page

- **GIVEN** the rail chatting a conversation of a field with a page
- **WHEN** the reader opens one from the list that is fixed to nothing
- **THEN** the conversation is drawn in the middle and the rail is the list again

### Requirement: A field keeps one notice

The system SHALL hold, for each field it offers, the last notice written to that
field, and SHALL answer it to whoever asks. A notice SHALL be a JSON object, and a
second notice SHALL replace the first whole rather than be merged into it. A field
SHALL keep a notice of its own, no field reading another's.

#### Scenario: A notice is written and read back

- **GIVEN** a field cora offers
- **WHEN** a notice is written to it and then asked for
- **THEN** what was written is answered

#### Scenario: A second notice

- **GIVEN** a field holding a notice naming two things
- **WHEN** a notice naming one of them is written
- **THEN** what is answered is the second notice alone

#### Scenario: One field's notice is not another's

- **GIVEN** two fields cora offers, each written a notice of its own
- **WHEN** each is asked for
- **THEN** each answers what was written to it

### Requirement: A notice says when cora heard it

The system SHALL record, on every notice it takes, the time it arrived by cora's own
clock, and SHALL answer that time with the notice. A time the writer states SHALL NOT
replace it, so no writer's clock has to agree with cora's.

#### Scenario: The arrival is answered with the notice

- **WHEN** a notice is written and then asked for
- **THEN** the answer carries the time cora took it

#### Scenario: A writer stating its own time

- **GIVEN** a notice carrying a time of the writer's own
- **WHEN** it is asked for
- **THEN** the time cora took it is the one the answer is stamped with

### Requirement: A field written to by nobody has no notice

The system SHALL answer that a field has no notice where none has been written, and
SHALL NOT treat that as a failure. A notice SHALL last as long as the process holding
it, and SHALL be gone when cora is started again.

#### Scenario: Nothing written yet

- **GIVEN** a field cora offers and nobody has written to
- **WHEN** its notice is asked for
- **THEN** the answer says there is none

#### Scenario: Cora is restarted

- **GIVEN** a field whose notice was written before cora was restarted
- **WHEN** its notice is asked for
- **THEN** the answer says there is none

### Requirement: A notice belongs to a field cora offers

The system SHALL refuse to hold or answer a notice for a name that is not a field of
the running composition, and SHALL say which fields there are. A field that arrives
with a plugin SHALL take a notice from that moment, and one whose plugin is gone
SHALL refuse both, the plugins folder being live.

#### Scenario: A name that is no field

- **WHEN** a notice is written to a name cora offers no field under
- **THEN** it is refused, and the refusal names the fields there are

#### Scenario: Asking for one

- **WHEN** the notice of a name that is no field is asked for
- **THEN** it is refused, and cora answers everything else as usual

#### Scenario: A field arrives with its plugin

- **GIVEN** a running cora, and a plugin bringing a field dropped into the folder
- **WHEN** a notice is written to that field
- **THEN** it is taken, with nothing restarted

### Requirement: A notice is small

The system SHALL refuse a notice larger than a few kilobytes, SHALL leave the held
notice unchanged when it does, and SHALL refuse a body that is not a JSON object.

#### Scenario: Too large

- **GIVEN** a field already holding a notice
- **WHEN** a notice past the ceiling is written
- **THEN** it is refused, and the held notice still answers

#### Scenario: Not an object

- **WHEN** a body that is not a JSON object is written
- **THEN** it is refused, and the held notice is unchanged

### Requirement: A field that speaks takes the screen

The shell SHALL ask each field that has a page for its notice, every few seconds. A
notice written after the last one that field was seen to hold SHALL open that field's
newest conversation, whatever the notice says — the shell reads that one was written and
nothing of what is in it. A field with no conversation pinned to it SHALL open nothing,
and neither SHALL a notice already standing when the page was loaded.

#### Scenario: A notice is written while the reader is elsewhere

- **GIVEN** a conversation pinned to a field with a page, and another conversation on
  the screen
- **WHEN** that field's notice is written
- **THEN** the pinned conversation is opened, and its field's page is what the screen is
  about

#### Scenario: The newest of several

- **GIVEN** two conversations pinned to that field
- **WHEN** its notice is written
- **THEN** the one that answered most recently is opened

#### Scenario: Already there

- **GIVEN** that field's conversation already on the screen
- **WHEN** its notice is written
- **THEN** the screen does not move

#### Scenario: A field nothing is pinned to

- **GIVEN** a field with a page and no conversation pinned to it
- **WHEN** its notice is written
- **THEN** nothing is opened and the reader is left where they were

#### Scenario: What was already standing

- **GIVEN** a field whose notice was written before the page was loaded
- **WHEN** the page loads
- **THEN** the screen stays on the conversation the address names

#### Scenario: A field with no page

- **GIVEN** a field that brought no page
- **WHEN** the shell asks for the notices
- **THEN** that field is not among them

#### Scenario: Nothing answering

- **GIVEN** a notice that cannot be read
- **WHEN** the shell asks for it
- **THEN** the rest of the page is unaffected and no banner is raised

### Requirement: A document is added from the composer

The page SHALL offer, beside the question being typed, a control that adds a file or a
photo to the field the conversation is in. It SHALL be the upload the rail already
makes: the same field, the same list, the same news and the same refusals. While an
upload is running the control SHALL say so and SHALL NOT start another.

#### Scenario: A file is added beside the question

- **GIVEN** a conversation in a field
- **WHEN** the reader adds a file from the composer
- **THEN** it is uploaded into that field and appears in that field's documents

#### Scenario: What it says while it runs

- **GIVEN** an upload started from the composer
- **WHEN** it has not finished
- **THEN** the control says an upload is running, and takes no second file

#### Scenario: A refusal is the same refusal

- **GIVEN** a file cora refuses
- **WHEN** it is added from the composer
- **THEN** the reader is told what the rail's control would have told them

### Requirement: The rail keeps the control it had

The rail's own control for adding a document SHALL remain where it is, over the list it
changes, so a reader working in the documents does not have to reach the conversation
to add one.

#### Scenario: Both controls add to the same field

- **GIVEN** a conversation fixed to a field
- **WHEN** a document is added from the rail and another from the composer
- **THEN** both are documents of that field

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
