As a reader deciding whether to load someone else's plugin,\
I want to be told that a plugin may put a page in my browser,\
so that I weigh what its script can reach before I drop it in.

## MODIFIED Requirements

### Requirement: The page says what loading a plugin costs in trust

The page SHALL say that a loaded plugin is arbitrary code running with the reader's own
permissions — instructions the model follows, tools it may call, handlers that can refuse
or amend, effects outside cora, and a page served in the reader's browser — and that this
is true of every harness of this kind. It SHALL say that such a page is script on cora's
own origin, so every route the reader's cora answers is open to it without a password.
It SHALL separate what cora enforces whatever a plugin does from what it does not.

#### Scenario: A reader decides whether to load someone else's plugin

- **WHEN** they read the page
- **THEN** it says a plugin runs with their own permissions, and names the five things it
  may contribute
- **AND** it names what the contract hands a plugin — the documents, what cora remembers
  including deleting it, and the model — and that none of that waits for approval, because
  the gate covers what changes outside cora

#### Scenario: A reader asks what a plugin's page may reach

- **WHEN** they read the page
- **THEN** it says the page is served on cora's own origin, that the API it may call is
  the one the reader holds, and that nothing approves a call the page makes

#### Scenario: A reader asks what holds regardless of the plugin

- **WHEN** they read the page
- **THEN** it names the approval gate before an effect, the untrusted label on retrieved
  and fetched text, the output confined to the configured directory, and the tool names a
  plugin may not take
- **AND** it names what cora does not enforce: no sandbox, no network restriction, and no
  review of what a plugin's instructions tell the model
