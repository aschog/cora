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
delegates may spend. A loop that reaches that bound SHALL report what it found, saying it
stopped early, rather than losing it or presenting it as complete. A loop that gathered
nothing SHALL refuse instead, so no write-up is asked of an empty transcript. The system SHALL report
the steps of that loop as children of the call that ran it, and SHALL require no change of
its own to allow it.

#### Scenario: A tool runs its own bounded loop

- **GIVEN** a plugin registering a tool that runs a model loop of its own
- **WHEN** the model calls that tool
- **THEN** the tool runs, and the turn is answered
- **AND** the loop is offered no tool of cora's that writes or stops the turn

#### Scenario: A loop spends what the host allows and no more

- **GIVEN** a loop asking for more rounds than the host allows, at any depth
- **WHEN** it runs
- **THEN** it is stopped at the host's allowance, and the turn's own is untouched

#### Scenario: A loop stopped at its ceiling reports what it has

- **GIVEN** a loop that spends its allowance without reaching an answer
- **WHEN** it stops
- **THEN** it reports what it found so far, and says it stopped early
- **AND** what it gathered is not discarded, and is not offered as a complete answer

#### Scenario: A loop that gathered nothing refuses rather than reporting

- **GIVEN** a loop stopped with nothing looked up in it
- **WHEN** it stops
- **THEN** it refuses, no write-up is asked for, and nothing is presented as a finding

#### Scenario: A spent allowance is not a model call per nested lookup

- **GIVEN** a loop whose allowance is gone, and a round that fans out many ways
- **WHEN** each nested lookup runs
- **THEN** none of them spends a model call of its own, however wide the fan-out

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

The system SHALL refuse a plugin it cannot load, and the refusal SHALL name the plugin
and what is wrong with it. A module defining no `extend`, one that raises while
registering, one registering a name cora has already taken, and two plugins whose names
end alike are each refused. A plugin SHALL be refused a name cora keeps for its own,
and a file or folder whose name is not a plain identifier SHALL be refused for that.
A dropped package importing what the environment does not hold SHALL be refused,
naming the folder and what went wrong — dependencies are not installed for it. Every
refusal SHALL name the plugin as it was found — a module by its path, a file or a
folder by its own name.

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

### Requirement: A plugin is found where it is, and says where it came from

The system SHALL load a plugin named as a module, wherever that module is installed
from, and SHALL load a single Python file dropped in its plugins folder with no
packaging at all. It SHALL likewise load a package directory dropped there — a folder
holding `__init__.py` — as one plugin, named for the folder, its own relative imports
resolving. Every plugin SHALL carry the source it was found through, and the
system SHALL name no plugin of its own in the code it ships.

#### Scenario: A named module living outside this repository is enough

- **GIVEN** a plugin module named in the environment, its code outside cora's own tree
- **WHEN** cora starts
- **THEN** it is loaded, and nothing cora ships names it

#### Scenario: A file in the plugins folder is enough

- **GIVEN** a single Python file in the plugins folder, with no manifest beside it
- **WHEN** cora starts
- **THEN** it is loaded, and the listing says which file it was read from

#### Scenario: A package folder in the plugins folder is enough

- **GIVEN** a directory in the plugins folder holding `__init__.py` and sibling modules
- **WHEN** cora starts
- **THEN** it is loaded under the folder's name, and the listing says which folder

#### Scenario: A dropped package's relative imports work as written

- **GIVEN** a dropped package whose `__init__.py` imports a sibling with `from . import`
- **WHEN** cora starts
- **THEN** the plugin loads, the sibling resolved from inside the folder

#### Scenario: A symlinked package is a plugin like any other

- **GIVEN** a symlink in the plugins folder pointing at a package directory elsewhere
- **WHEN** cora starts, and the linked package is later edited where it lives
- **THEN** it loads under the link's name, and the edit reaches the next composition

#### Scenario: A folder without __init__.py is not a plugin

- **GIVEN** a directory in the plugins folder holding no `__init__.py`
- **WHEN** cora starts
- **THEN** the folder is ignored, and the deployment loads without it

#### Scenario: A named module says it was named

- **GIVEN** plugins loaded from both sources
- **WHEN** the listing is read
- **THEN** a named module is shown under its module path, and a file under its folder

### Requirement: The plugins folder is live

The system SHALL keep its running plugin set in step with the plugins folder while it
serves: a plugin dropped in is installed, one deleted is removed, and one edited is
reloaded, each visible by the next request without a restart. A turn already running
SHALL finish on the set it started with. Plugins named as modules in the environment
SHALL stay as started; only the folder is live. A folder state that cannot load SHALL
refuse every request, readably and naming the plugin, for as long as it holds; the set
already composed SHALL be kept, and SHALL serve again as soon as the folder loads.

#### Scenario: A dropped plugin is installed without a restart

- **GIVEN** a running deployment, and a plugin then dropped into the folder
- **WHEN** the plugin listing is next read
- **THEN** the new plugin is in it, and its tools answer the next question

#### Scenario: A deleted plugin is removed without a restart

- **GIVEN** a running deployment loaded from the folder, and the plugin then deleted
- **WHEN** the plugin listing is next read
- **THEN** the plugin is gone, and nothing offers its tools

#### Scenario: An edited plugin serves its new behaviour

- **GIVEN** a running deployment, and a dropped plugin's code then changed
- **WHEN** the next turn runs
- **THEN** the plugin acts as the new code says

#### Scenario: A broken drop does not take the deployment down

- **GIVEN** a running deployment, and a file dropped that cannot load
- **WHEN** the next request arrives, and another after the file is removed
- **THEN** the first is refused naming the plugin, and the second is served by the
  prior set, nothing lost

#### Scenario: A turn in flight is not reshaped under itself

- **GIVEN** a turn already running when the folder changes
- **WHEN** that turn completes
- **THEN** it finishes on the plugin set it started with

### Requirement: A field is offered by whatever brings it

The system SHALL offer a field if anything brings it: a registration of any loaded
plugin — named in the environment or dropped in the folder alike — or the deployment's
configuration, which is how a field with no plugin behind it, a documents-only field,
exists. What a reader may pick and pin, what a question may be routed to, and what the
rails may list and upload into SHALL be that one set, each field named once, and a
plugin's field SHALL go when the plugin goes. Deploying a plugin SHALL need no
configuration at all.

#### Scenario: A dropped plugin's field is offered without configuration

- **GIVEN** a running deployment, and a plugin dropped that registers under `interview`
- **WHEN** the offered fields are next read
- **THEN** `interview` is among them, though no configuration names it

#### Scenario: A named module's field is offered the same way

- **GIVEN** a module named in the environment registering under a field nothing else
  names
- **WHEN** the offered fields are read
- **THEN** that field is among them

#### Scenario: A configured field with no plugin is still a field

- **GIVEN** a deployment whose configuration names a field no registration carries
- **WHEN** the offered fields are read
- **THEN** it is among them, holding documents and nothing else

#### Scenario: A deleted plugin takes its field with it

- **GIVEN** a deployment offering a field only a dropped plugin registered
- **WHEN** the plugin is deleted and the offered fields are next read
- **THEN** the field is gone with it

#### Scenario: A question is answered in the dropped field

- **GIVEN** a dropped plugin whose field no configuration names
- **WHEN** a conversation is pinned to that field and a question asked
- **THEN** the turn runs in it, and is not refused as a field nobody offers

### Requirement: Cora says what it loaded

The system SHALL offer one listing of every plugin it loaded, naming for each its
source, the scopes it registered under, its tools by name, whether it heads a section
of the brief, and the events it subscribed to. A registration carrying no scope SHALL
be flagged as system-wide, because it is a claim on every turn. The listing SHALL be
readable in a terminal and on the screen, and both SHALL say the same thing.

#### Scenario: Each plugin is listed with what it registered

- **GIVEN** several plugins loaded from different sources
- **WHEN** the listing is read
- **THEN** each is named with its source, its scopes, its tools, its instructions and
  its events

#### Scenario: A system-wide registration is flagged

- **GIVEN** a plugin registering one thing system-wide and the rest under a scope
- **WHEN** the listing is read
- **THEN** the system-wide one is marked as such, and the scoped ones are not

#### Scenario: The same listing is on the screen

- **GIVEN** the shell serving the page
- **WHEN** the page asks what is loaded
- **THEN** it is given what the terminal listing shows, plugin for plugin

#### Scenario: A bare cora says it is bare

- **GIVEN** a deployment that named no plugin and dropped no file
- **WHEN** the listing is read
- **THEN** it says that nothing is loaded, rather than showing nothing

### Requirement: The contract has a version, and a plugin says which it wants

The system SHALL read the contract version a plugin declares before calling `extend`,
and SHALL refuse one it does not offer. The refusal SHALL name the version the plugin
asked for and the version cora offers. A plugin declaring none SHALL be taken as asking
for the version cora offers.

#### Scenario: A version cora does not offer is refused

- **GIVEN** a plugin declaring a contract version cora does not support
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

### Requirement: A plugin is a distribution, not a fork

The system SHALL name no plugin and no scope in the code it ships, so that a field is
added by installing a distribution rather than by editing cora. Every plugin cora ships
SHALL be readable as one such distribution and nothing more.

#### Scenario: The core names no plugin and no scope

- **WHEN** everything cora ships is read
- **THEN** no file names a plugin or one of the fields a plugin registers under

#### Scenario: The travel plugin is a distribution

- **GIVEN** the contract, complete
- **WHEN** the travel plugin is read back against it
- **THEN** it registers through the contract alone, and cora ships nothing for its sake

### Requirement: A tool says whether it changes anything outside cora

A plugin registering a tool SHALL be able to declare that calling it changes something
outside cora. The declaration SHALL belong to the tool, and a tool declaring nothing SHALL
be taken as changing nothing.

#### Scenario: A tool is registered as having an effect

- **GIVEN** a plugin registering a tool that declares one
- **WHEN** the plugins are listed
- **THEN** that tool is shown as having an effect, and its neighbours are not

#### Scenario: A tool declaring nothing is read as changing nothing

- **GIVEN** a tool registered without the declaration
- **WHEN** a turn offers it
- **THEN** it is treated as reading only

### Requirement: A sub-agent reads and does not act

The system SHALL offer a delegated loop no tool that declares an effect, and no tool of
its own that writes or stops a turn. A loop SHALL therefore be unable to propose an effect
or to stop and ask, whatever the plugin that ran it passed in.

#### Scenario: An effect is withheld from a delegated loop

- **GIVEN** a scope holding both a researcher and a tool that declares an effect
- **WHEN** the researcher runs
- **THEN** the effecting tool is not among the tools it is offered
- **AND** the plugin is told which of its tools was withheld

#### Scenario: A sub-agent cannot stop the turn to ask

- **GIVEN** a delegated loop, running
- **WHEN** the tools it may call are read
- **THEN** nothing among them stops the turn, and nothing among them writes

#### Scenario: The rule is asserted rather than described

- **GIVEN** the tools a delegated loop is offered, whatever was passed to it
- **WHEN** a guard reads them
- **THEN** it fails if any writes, stops the turn, or declares an effect

### Requirement: The travel scope ships a researcher

The travel scope SHALL offer a tool that researches a question over several lookups and
answers with one report. How many rounds it may spend SHALL be the deployment's to set,
read from the plugin's own settings.

#### Scenario: A broad question is researched rather than answered in one pass

- **GIVEN** the travel scope, with its documents and its forecast tool
- **WHEN** a question needs several lookups
- **THEN** the researcher runs a loop of its own, and the answer rests on what it found

#### Scenario: The conversation carries the report

- **GIVEN** a turn whose researcher made several lookups
- **WHEN** what the turn's model was told is read
- **THEN** it holds the report, and not each lookup that produced it

#### Scenario: The trace holds what the conversation does not

- **GIVEN** the same turn
- **WHEN** its trace is read
- **THEN** the researcher's lookups are there, nested under the call that started them

#### Scenario: The rounds are the deployment's to set

- **GIVEN** a deployment naming a number of rounds in the plugin's own settings
- **WHEN** the researcher runs
- **THEN** what it may spend follows that number, and the host's own ceiling still
  bounds it

### Requirement: A plugin keeps what it worked out, for the length of a conversation

A plugin SHALL be able to keep text under a name of its choosing, and read it back on a
later turn of the same conversation. A name nothing was kept under SHALL read as
nothing, rather than as a failure.

#### Scenario: What one turn kept, the next turn reads

- **GIVEN** a plugin whose tool keeps a value under a name
- **WHEN** a later turn of that conversation calls a tool that reads the name
- **THEN** the value it kept comes back

#### Scenario: Another conversation reads nothing

- **GIVEN** a plugin that kept a value in one conversation
- **WHEN** its tool reads that name in a second conversation
- **THEN** nothing comes back, and the first conversation still holds its value

#### Scenario: A name nothing was kept under

- **GIVEN** a plugin that has kept nothing
- **WHEN** its tool reads any name
- **THEN** nothing comes back and the turn answers

#### Scenario: Keeping nothing under a name drops it

- **GIVEN** a plugin that kept a value under a name
- **WHEN** its tool keeps nothing under that same name
- **THEN** a later read of it comes back with nothing

### Requirement: What a plugin keeps is its own

Names SHALL be held per plugin. One plugin SHALL NOT read or overwrite what another
kept, whichever name either chose.

#### Scenario: Two plugins use the same name

- **GIVEN** two plugins that each keep a different value under the name `plan`
- **WHEN** each reads `plan` in the same conversation
- **THEN** each reads back its own value

### Requirement: A plugin outside a turn keeps nothing

Reading or writing outside a tool call SHALL come back with nothing and record nothing,
because there is no conversation for it to belong to.

#### Scenario: A plugin writes while it is being loaded

- **GIVEN** a plugin that keeps a value inside its own `extend`
- **WHEN** a turn later reads that name
- **THEN** nothing comes back, and loading the plugin did not fail

### Requirement: What a plugin kept goes when the conversation goes

Deleting a conversation SHALL delete what its plugins kept in it, as it deletes the
turns and the thread they were answered on.

#### Scenario: A deleted conversation keeps nothing behind

- **GIVEN** a conversation in which a plugin kept a value
- **WHEN** that conversation is deleted
- **THEN** a new conversation on that thread reads nothing under the name

#### Scenario: Deleting one conversation leaves another alone

- **GIVEN** two conversations in which the same plugin kept different values
- **WHEN** one of them is deleted
- **THEN** the other still reads back its own value

### Requirement: A plugin says what it did, and the reader reads it

A plugin SHALL be able to contribute one line saying what it just did, with detail
behind it for a reader who opens it. The line SHALL name the plugin that took it.

#### Scenario: A plugin's own work is on the trace

- **GIVEN** a plugin whose tool says what it did while the call runs
- **WHEN** the turn is answered
- **THEN** the trace carries that line, naming the plugin

#### Scenario: The detail is behind the line

- **GIVEN** a plugin that says what it did and gives detail with it
- **WHEN** the reader opens that step
- **THEN** the detail it gave is what they read

### Requirement: What a plugin shows lands under the call it happened in

A line a plugin contributes during a tool call SHALL appear among that call's own steps,
beside the rounds a delegated loop reports there.

#### Scenario: Shown under the call, not beside it

- **GIVEN** a plugin whose tool shows two lines and delegates a loop once
- **WHEN** the turn is answered
- **THEN** all three stand under that one call, and none beside it

#### Scenario: Shown outside a call is dropped

- **GIVEN** a plugin that shows a line while it is being loaded
- **WHEN** a turn is answered afterwards
- **THEN** the trace carries no such line, and loading the plugin did not fail

### Requirement: A plugin cannot sign another plugin's name

The name on the line SHALL be the name cora loaded that plugin under, whatever the
plugin passes.

#### Scenario: A plugin names itself something else

- **GIVEN** a plugin that tries to show a line under another plugin's name
- **WHEN** the turn is answered
- **THEN** the line names the plugin that showed it

### Requirement: A plugin may show that something went wrong

A plugin SHALL be able to mark what it shows as having failed, and the trace SHALL show
it as a failed step without ending the turn.

#### Scenario: A failed line is shown as failed

- **GIVEN** a plugin whose loop shows a line marked as gone wrong
- **WHEN** the turn is answered
- **THEN** that step reads as failed and the turn still answers

### Requirement: A plugin sees the answer before the reader does

A plugin SHALL be able to subscribe to the answer being settled, and SHALL be given it
as text. What it hands back SHALL be what the reader is given, and handing back nothing
SHALL leave the answer as it was.

#### Scenario: An answer is redacted before it is handed over

- **GIVEN** a plugin subscribed to the answer, replacing a phone number with a marker
- **WHEN** a turn answers with a phone number in it
- **THEN** the reader is given the answer with the marker, and the number is nowhere in it

#### Scenario: A handler that changes nothing changes nothing

- **GIVEN** a plugin subscribed to the answer that hands back nothing
- **WHEN** a turn answers
- **THEN** the reader is given the answer exactly as the model wrote it

### Requirement: Amendments to the answer chain in load order

Each subscribed handler SHALL be given what the one before it returned, so two plugins
both change the answer and neither undoes the other.

#### Scenario: Two plugins each change the answer

- **GIVEN** one plugin that redacts and a second that appends a notice, loaded in that order
- **WHEN** a turn answers
- **THEN** the reader is given an answer that is both redacted and carries the notice

### Requirement: A broken check costs the turn nothing

A handler that raises, or that hands back something that is not text, SHALL be dropped
and the turn SHALL still answer.

#### Scenario: A handler raises

- **GIVEN** a plugin subscribed to the answer whose handler raises
- **WHEN** a turn answers
- **THEN** the reader is given the answer, and the trace says that plugin could not change it

#### Scenario: A handler hands back something that is not text

- **GIVEN** a plugin subscribed to the answer that hands back a number
- **WHEN** a turn answers
- **THEN** the answer stands unchanged and the trace records the failure

### Requirement: The citations follow the answer that was amended

Citations SHALL be read off the answer as it was amended. A claim removed by a handler
SHALL take its citation with it.

#### Scenario: A redacted sentence drops its citation

- **GIVEN** an answer citing two passages, and a plugin that removes the sentence carrying the second
- **WHEN** the turn is answered
- **THEN** the reader is given one citation, and it is the one still cited

### Requirement: The trace names the plugin that changed the answer

A handler that changes the answer SHALL appear on the trace, named for its plugin, as a
handler at any other point does.

#### Scenario: A reader sees who changed it

- **GIVEN** a plugin that redacted the answer
- **WHEN** the reader opens the trace
- **THEN** a step names that plugin and says it changed the answer
