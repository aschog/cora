As someone who wrote a plugin for my own field,\
I want to install it or drop it in a folder and have cora find it,\
so that using it does not mean forking cora.

## ADDED Requirements

### Requirement: A plugin is found where it is, and says where it came from

The system SHALL load a plugin named as a module, wherever that module is installed
from, and SHALL load a single Python file dropped in its plugins folder with no
packaging at all. Every plugin SHALL carry the source it was found through, and the
system SHALL name no plugin of its own in the code it ships.

#### Scenario: A named module living outside this repository is enough

- **GIVEN** a plugin module named in the environment, its code outside cora's own tree
- **WHEN** cora starts
- **THEN** it is loaded, and nothing cora ships names it

#### Scenario: A file in the plugins folder is enough

- **GIVEN** a single Python file in the plugins folder, with no manifest beside it
- **WHEN** cora starts
- **THEN** it is loaded, and the listing says which file it was read from

#### Scenario: A named module says it was named

- **GIVEN** plugins loaded from both sources
- **WHEN** the listing is read
- **THEN** a named module is shown under its module path, and a file under its folder

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

## MODIFIED Requirements

### Requirement: A plugin cora cannot have is refused by name

The system SHALL refuse a plugin it cannot load, and the refusal SHALL name the plugin
and what is wrong with it. A module defining no `extend`, one that raises while
registering, one registering a name cora has already taken, and two plugins whose names
end alike are each refused. A plugin SHALL be refused a name cora keeps for its own,
and a file whose stem is not a plain identifier SHALL be refused for that. Every refusal
SHALL name the plugin as it was found — a module by its path, a file by its own.

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
