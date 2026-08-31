# plugins Specification

## Purpose

How everything cora knows and can do arrives: a module is handed cora, registers what it
has, takes part in the turn at the points it subscribed to, and is refused by name when
it cannot be had.

## Requirements

### Requirement: A plugin registers what it has

The system SHALL load a plugin by calling `extend` on its module, and SHALL offer
whatever that call registered: its tools callable, its instructions in the brief, its
handlers taking part in the turn. The system SHALL accept no other way of contributing,
and SHALL offer no separate way to screen what the user types.

#### Scenario: A plugin registers rather than declares

- **GIVEN** a module defining `extend(cora)` and no record of contributions
- **WHEN** it is loaded
- **THEN** its tools are callable, its instructions are in the brief, and its handlers run

#### Scenario: The plugins cora ships carry no record

- **GIVEN** the security and fitness plugins as they are shipped
- **WHEN** their modules are read
- **THEN** each registers through `extend`, and neither leaves a record behind

#### Scenario: Screening is a subscription like any other

- **GIVEN** a plugin that wants to refuse what the user typed
- **WHEN** it registers
- **THEN** it subscribes to the screening event, there being no other way to ask

### Requirement: A plugin subscribes to a named point in the turn

The system SHALL let a plugin subscribe a handler to a named event: the question being
screened, the brief being settled, a tool call about to run, and a tool result coming
back. A handler SHALL be handed only frozen values and SHALL answer by returning — a
refusal, an amendment, or nothing. The system SHALL accept no handler that writes the
turn's state, and SHALL refuse a subscription to an event it does not have.

#### Scenario: A handler amends what the model is told

- **GIVEN** a plugin subscribing to the brief being settled
- **WHEN** a turn runs in its scope
- **THEN** what the handler returned is in the brief the model reads

#### Scenario: A handler refuses a call before it runs

- **GIVEN** a plugin subscribing to the tool-call event and refusing one tool
- **WHEN** the model asks for that tool
- **THEN** the tool does not run, the model is told why, and the turn answers anyway

#### Scenario: A handler wraps what a tool returned

- **GIVEN** a plugin subscribing to a tool result coming back
- **WHEN** a tool it applies to returns
- **THEN** the model is told what the handler returned, not what the tool did

#### Scenario: What a handler is handed, it may read and not keep

- **GIVEN** a plugin whose handler rewrites the arguments of a call it is shown
- **WHEN** that call runs
- **THEN** it runs on the arguments the model asked for

#### Scenario: A handler cannot unlabel the user's own documents

- **GIVEN** a plugin whose handler replaces a passage with prose of its own
- **WHEN** the model is told what the tool returned
- **THEN** it is told behind the notice that says the material is the user's, not cora's

#### Scenario: A handler answers one call, and not another

- **GIVEN** a plugin whose handler answers with a result belonging to another call
- **WHEN** the round reads what came back
- **THEN** the call it made is the call that was answered

#### Scenario: A handler that returns nothing changes nothing

- **GIVEN** a plugin whose handler reads what it is handed and returns nothing
- **WHEN** a turn runs
- **THEN** the turn is unchanged, and the handler saw what it subscribed to

#### Scenario: An event cora does not have is refused by name

- **GIVEN** a plugin subscribing to an event cora does not name
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the event it asked for

### Requirement: Cora's own screen is a subscriber

The system SHALL run its own screening of what the user types as handlers on the same
event a plugin subscribes to, registered the same way and system-wide. It SHALL reach
them no other way.

#### Scenario: Cora's own screening runs as handlers

- **GIVEN** cora's own input rules and a plugin's, both loaded
- **WHEN** a turn runs
- **THEN** all of them ran as handlers on the screening event
- **AND** nothing in cora reached its own rules by another path

#### Scenario: Cora's own handlers run first

- **GIVEN** cora's own screening and a plugin's, both refusing the same question
- **WHEN** the turn runs
- **THEN** the refusal the user reads is cora's

### Requirement: Handlers chain in load order, and the trace names each plugin

The system SHALL run the handlers on one event in a stated order — its own first, then
the plugins as they were loaded — and each amendment SHALL be handed what the one before
it returned. The trace SHALL name the plugin behind every amendment and every refusal.

#### Scenario: Two handlers amend the same event

- **GIVEN** two plugins subscribing to the brief being settled
- **WHEN** a turn runs where both apply
- **THEN** the second was handed what the first returned, and the brief holds both

#### Scenario: The trace attributes an amendment to its plugin

- **WHEN** the trace of that turn is read
- **THEN** each amendment is named as that plugin's, in the order they ran

### Requirement: A handler fails closed when it refuses and open when it amends

The system SHALL treat a handler that raises on a refusing event as a refusal, so a
question or a call is never let through by a broken rule. A handler that raises on any
other event SHALL be dropped and the turn SHALL carry on without it. The trace SHALL
name the plugin in both cases.

#### Scenario: A screening handler that raises refuses the turn

- **GIVEN** a plugin whose screening handler raises
- **WHEN** a turn runs
- **THEN** the question is refused, and the trace names that plugin

#### Scenario: An amender that raises is dropped

- **GIVEN** a plugin whose brief handler raises
- **WHEN** a turn runs
- **THEN** the turn completes without that amendment, and the trace names that plugin

#### Scenario: An observer that raises is dropped

- **GIVEN** a plugin whose handler only watches, and raises
- **WHEN** a turn runs
- **THEN** the turn completes unchanged, and the trace names that plugin

#### Scenario: What a handler was holding stays out of what the user reads

- **GIVEN** a plugin whose handler raises carrying a value of its own
- **WHEN** the refusal or the trace is read
- **THEN** neither quotes what the handler was holding

### Requirement: A registration has a scope, and a system-wide one cannot be removed

Every registration SHALL carry a scope, and one carrying none SHALL be system-wide. The
system SHALL apply a registration when it is system-wide or when its scope is among the
turn's active ones, and SHALL offer no way for a scope to switch a system-wide one off.

#### Scenario: A scoped handler applies where it belongs

- **GIVEN** a handler registered under a named scope
- **WHEN** a turn runs in a different scope
- **THEN** it does not run

#### Scenario: A system-wide screen cannot be scoped away

- **GIVEN** a system-wide plugin loaded beside two scopes
- **WHEN** an injection attempt arrives in either scope, or with no scope active
- **THEN** it is refused before the model is called

#### Scenario: One plugin registers under two lifetimes

- **GIVEN** the fitness plugin, whose instructions and tools are its scope's
- **WHEN** its medical filter is registered
- **THEN** the filter is system-wide, and the instructions and tools are not

#### Scenario: The medical filter applies outside the scope it came from

- **GIVEN** the fitness plugin loaded
- **WHEN** a medical question is asked in another scope, or with no scope active
- **THEN** it is refused

### Requirement: A turn runs under the scopes it was given

The system SHALL run a turn under the scope its conversation is pinned to, or the one its
caller named, or the one it routed the question to. A deployment SHALL name in the
environment the scopes a turn may run under, and a deployment naming one SHALL leave
routing nothing to choose. A turn SHALL keep the scope it settled on for as long as it
lasts.

#### Scenario: The deployment says what its cora is for

- **GIVEN** a deployment naming one scope beside the plugins it loaded
- **WHEN** anyone asks anything
- **THEN** that scope's instructions and tools are what the turn runs with, unrouted

#### Scenario: The caller of one turn says otherwise

- **GIVEN** the same deployment
- **WHEN** a turn is asked for under a scope of its own
- **THEN** it runs under that one instead

#### Scenario: The pin outranks the reading of the question

- **GIVEN** a conversation pinned to one of two available scopes
- **WHEN** a question belonging to the other is asked
- **THEN** the turn runs under the pinned scope, and the question is not routed

#### Scenario: A turn that stopped to ask resumes under the same scopes

- **GIVEN** a scoped turn that stopped to put a decision to the user
- **WHEN** it is resumed
- **THEN** the rest of it runs under the scopes it started under

### Requirement: A plugin is handed cora's own parts

The host SHALL give a plugin what cora has: document search, what cora remembers, and
the model itself. It SHALL also give the plugin a log and settings of its own, both
named for the plugin rather than for cora.

#### Scenario: A plugin uses cora's own parts

- **GIVEN** a plugin that wants to search, to remember, or to call the model
- **WHEN** it is loaded
- **THEN** the host it was handed offers each of those

#### Scenario: What a plugin logs and reads is named for it

- **GIVEN** a loaded plugin that writes a log line and reads a setting
- **WHEN** the line is written and the setting is read
- **THEN** both are named for that plugin

### Requirement: A registered tool may run a turn of its own

A tool SHALL be able to run its own bounded loop with the model, offered cora's document
search and the tools the plugin passed it. The system SHALL offer such a loop none of its
own tools that write or stop a turn, and SHALL bound what one loop and everything it
delegates may spend. The system SHALL report the steps of that loop as children of the
call that ran it, and SHALL require no change of its own to allow it.

#### Scenario: A tool runs its own bounded loop

- **GIVEN** a plugin registering a tool that runs a model loop of its own
- **WHEN** the model calls that tool
- **THEN** the tool runs, and the turn is answered
- **AND** the loop is offered no tool of cora's that writes or stops the turn

#### Scenario: A loop spends what the host allows and no more

- **GIVEN** a loop asking for more rounds than the host allows, at any depth
- **WHEN** it runs
- **THEN** it is stopped at the host's allowance, and the turn's own is untouched

#### Scenario: The loop's steps are shown under the call

- **WHEN** the trace of that turn is read
- **THEN** the loop's steps are children of the call, in the order they were taken

#### Scenario: What a loop read is named rather than numbered

- **GIVEN** a loop that searched the user's documents
- **WHEN** it answers
- **THEN** it was shown each passage under its document's name, as the document was
  written
- **AND** what it answered carries no citation number of its own

### Requirement: A plugin cora cannot have is refused by name

The system SHALL refuse a plugin it cannot load, and the refusal SHALL name the module
and what is wrong with it. A module defining no `extend`, one that raises while
registering, one registering a name cora has already taken, and two modules whose names
end alike are each refused.

#### Scenario: A module that does not register is refused

- **GIVEN** a module defining no `extend`
- **WHEN** cora starts
- **THEN** it refuses, naming that module and saying it registers nothing

#### Scenario: A module that fails while registering is refused

- **GIVEN** a module whose `extend` raises
- **WHEN** cora starts
- **THEN** it refuses, naming that module and what went wrong inside it

#### Scenario: A name cora has already taken is refused

- **GIVEN** a module registering a tool under a name cora offers itself
- **WHEN** cora starts
- **THEN** it refuses, naming that module and the name it may not take

#### Scenario: Two plugins that cannot be told apart are refused

- **GIVEN** two modules whose paths end in the same name
- **WHEN** cora starts
- **THEN** it refuses, naming both and the name they share

### Requirement: What a plugin read for cora is labelled untrusted

The system SHALL label as untrusted whatever reaches a model out of the user's documents.
This SHALL hold for the passages a plugin's own loop read, for what that loop answered
after reading them, and for a plugin that searched the documents itself.

#### Scenario: A delegated loop reads its passages behind the label

- **GIVEN** a loop that searched the user's documents
- **WHEN** it is shown what the search found
- **THEN** the passages arrive labelled untrusted, as a turn's own search labels them

#### Scenario: What a loop answered reaches the turn labelled

- **GIVEN** a tool whose loop read the documents and answered in its own words
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted, though it carries no passage

#### Scenario: A plugin that searches for itself says so

- **GIVEN** a plugin whose tool searches the documents without delegating
- **WHEN** the turn's model is told what that tool returned
- **THEN** the answer arrives labelled untrusted
