As a plugin author,\
I want dropping my plugin — one file or its whole folder — into the plugins folder
to be enough,\
so that it is installed as it is: no packaging, no environment change, no restart.

## ADDED Requirements

### Requirement: The plugins folder is live

The system SHALL keep its running plugin set in step with the plugins folder while it
serves: a plugin dropped in is installed, one deleted is removed, and one edited is
reloaded, each visible by the next request without a restart. A turn already running
SHALL finish on the set it started with. Plugins named as modules in the environment
SHALL stay as started; only the folder is live. A folder state that cannot load SHALL
refuse the request that met it, readably, and the set already running SHALL keep
serving until the folder loads again.

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
- **WHEN** the next request arrives
- **THEN** it is refused naming the plugin, and the prior set still serves

#### Scenario: A turn in flight is not reshaped under itself

- **GIVEN** a turn already running when the folder changes
- **WHEN** that turn completes
- **THEN** it finishes on the plugin set it started with

## MODIFIED Requirements

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

#### Scenario: A folder without __init__.py is not a plugin

- **GIVEN** a directory in the plugins folder holding no `__init__.py`
- **WHEN** cora starts
- **THEN** the folder is ignored, and the deployment loads without it

#### Scenario: A named module says it was named

- **GIVEN** plugins loaded from both sources
- **WHEN** the listing is read
- **THEN** a named module is shown under its module path, and a file under its folder

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
