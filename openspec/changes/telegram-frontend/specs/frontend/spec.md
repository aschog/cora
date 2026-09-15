As someone away from the machine cora runs on,\
I want to ask it from Telegram,\
so that I get my answer where I already am.

## REMOVED Requirements

### Requirement: cora is used through one screen

**Reason**: The rule counted frontends, and a count is not what the Streamlit removal was
about — it was about code nobody runs. The rule below holds every frontend to that
instead, which is what lets a second one ship.

**Migration**: One process for the page and the API is carried into the requirement
below unchanged. The scenario about Streamlit is carried as the rule that catches it —
no shipped file imports a framework its own portion was not given — because that is the
check the repository really has, and it holds of the next removed frontend too.

## ADDED Requirements

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
