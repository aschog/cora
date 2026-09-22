As a stranger opening the repository,\
I want the one screen I read to also be the one that tells me how to run it,\
so that I never follow a link to a page that is no longer there.

## ADDED Requirements

### Requirement: The front door opens with what cora is for

The system SHALL open `README.md` with what problem cora solves and who it is for, and
SHALL link the showcase entry near the top.

#### Scenario: A stranger reads the first screen

- **WHEN** someone who has never seen cora reads the first screen of `README.md`
- **THEN** they can say what problem it solves and who it is for
- **AND** the showcase entry is linked near the top

### Requirement: The front door carries the commands

The system SHALL state in `README.md` the commands that install cora, load its plugins,
run it, and run its gates, rather than linking a page that holds them. `README.md` SHALL
link no page under `docs/` that the repository does not carry.

#### Scenario: A reader installs and runs cora

- **WHEN** a reader reaches installing or running cora
- **THEN** `README.md` gives the commands themselves, and links no page for them

#### Scenario: Every link the front door makes resolves

- **WHEN** a reader follows a `docs/` link from `README.md`
- **THEN** the file it names is one the repository holds

### Requirement: The front door says what a plugin must export

The system SHALL state in `README.md` what a plugin must export, where it is dropped to
be loaded, and how its settings are named, and SHALL name the plugins under `plugins/`
as the worked examples rather than restating them.

#### Scenario: A reader writes their first plugin

- **WHEN** a reader reaches the subject of writing a plugin
- **THEN** `README.md` names `extend` as what it must export, `.cora/plugins/` as where
  it is dropped, and the `CORA_PLUGIN_<NAME>_<SETTING>` form its settings take

## REMOVED Requirements

### Requirement: The front door says what cora is for

**Reason**: It bundled two concerns, and only one survives. What the README opens with
is still required; that it carry no instruction a page of its own holds is now false,
because no page holds one.

**Migration**: The surviving half is *The front door opens with what cora is for*, above,
with its scenario carried over unchanged. The half that inverted is *The front door
carries the commands*.

### Requirement: The site describes itself

**Reason**: There is no site. The built pages, `mkdocs.yml` and the generated reference
are gone, so a description every page carries is a description of nothing.

**Migration**: What the site said about cora, `README.md` says. What it is made of, the
tree under `src/cora/` says, with the generated maps under `docs/assets/` for how a turn
moves through it. Nothing is published, so nothing needs a description to publish with.

### Requirement: What the docs name, cora has

**Reason**: The guard read the pages, and the pages are gone. `README.md` is the only
prose left naming a `CORA_*` variable or a `make` target, and it is one file a reader
holds rather than a tree a test has to sweep.

**Migration**: None. `tests/guards/test_docs.py` is deleted with the pages it read.
