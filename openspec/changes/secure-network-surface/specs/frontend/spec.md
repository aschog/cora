As an operator,\
I want deliberate, authenticated network access to cora,\
so that remote access does not expose my data or tools.\

## ADDED Requirements

### Requirement: Loopback remains the default

The HTTP server SHALL default to `127.0.0.1:8000` without requiring an access token.
Explicit loopback binding SHALL remain token-free when network mode is disabled.

#### Scenario: Default startup

- **GIVEN** no network, host, port, or token settings
- **WHEN** the HTTP server starts
- **THEN** it binds to `127.0.0.1:8000` and answers without authentication

#### Scenario: Explicit loopback startup

- **GIVEN** network mode is disabled
- **WHEN** startup selects `localhost`, an IPv4 loopback address, or `::1`
- **THEN** it allows startup without a token

### Requirement: Network access is an explicit protected mode

Non-loopback startup SHALL require `CORA_NETWORK=1` and a nonblank `CORA_API_TOKEN`.
Network mode SHALL require authentication even when binding to loopback.
Invalid network settings SHALL refuse startup before assembling the app, without printing credentials.

#### Scenario: Public binding without opt-in

- **GIVEN** `CORA_HOST=0.0.0.0` without `CORA_NETWORK=1`
- **WHEN** the HTTP server starts
- **THEN** it refuses startup and names the required opt-in

#### Scenario: Non-loopback names and addresses

- **GIVEN** a non-loopback address or a hostname other than `localhost`
- **WHEN** startup has no network opt-in
- **THEN** it refuses startup

#### Scenario: Network mode without a token

- **GIVEN** `CORA_NETWORK=1` with a missing or blank `CORA_API_TOKEN`
- **WHEN** the HTTP server starts
- **THEN** it refuses startup and names the missing token setting

#### Scenario: Protected startup

- **GIVEN** `CORA_NETWORK=1` and a nonblank API token
- **WHEN** the HTTP server starts on a selected host and port
- **THEN** it serves an authenticated HTTP surface at that address

#### Scenario: Invalid opt-in

- **GIVEN** `CORA_NETWORK` contains something other than blank, `0`, or `1`
- **WHEN** the HTTP server starts
- **THEN** it refuses startup and names the invalid setting without printing tokens

### Requirement: Network credentials protect the entire HTTP surface

In network mode, every HTTP route SHALL require valid credentials before reading data or running app operations.
Missing, malformed, or incorrect credentials SHALL return `401` without disclosing protected content.
The API token SHALL grant access through Bearer authentication or Basic authentication with username `cora`.
The served browser page SHALL offer native HTTP login, without putting credentials into URLs or page content.

#### Scenario: Missing or invalid credentials

- **GIVEN** network mode and requests lacking valid credentials
- **WHEN** API routes, uploads, field files, plugin pages, or built UI assets are requested
- **THEN** they return `401` without serving protected content or performing mutations

#### Scenario: API access

- **GIVEN** network mode and a valid Bearer API token
- **WHEN** a client lists fields or writes a notice
- **THEN** the request follows the normal route contract

#### Scenario: Browser access

- **GIVEN** network mode and a built page
- **WHEN** a reader opens cora and authenticates as `cora` using the API token
- **THEN** the page, same-origin API requests, and plugin frames remain usable

#### Scenario: Streaming access

- **GIVEN** network mode and valid API credentials
- **WHEN** a question is asked
- **THEN** its answer streams as before and disconnecting still stops the turn

### Requirement: Browser credentials cannot authorize foreign-origin mutations

In network mode, authenticated mutation requests carrying a foreign or null Origin SHALL be refused before changing state.
Same-origin requests and native clients without an Origin SHALL retain authenticated access.

#### Scenario: Foreign-origin upload

- **GIVEN** valid API credentials and a document upload from a different browser origin
- **WHEN** the upload is submitted
- **THEN** it returns `403` and keeps no document

#### Scenario: Native client

- **GIVEN** valid API credentials and no Origin header
- **WHEN** a client writes a notice
- **THEN** the notice is accepted

### Requirement: Network operators know what they expose

The README SHALL explain network opt-in, token configuration, native browser login, and deferred watch compatibility.
It SHALL name the exposed data, plugin pages, mutations, and model-driven shell access available to API-token holders.
It SHALL warn that HTTP exposes credentials in transit and recommend trusted networks or HTTPS termination.
It SHALL explain that changing credentials requires restarting cora.
It SHALL state that existing watch commands and requests lack the required network opt-in or authentication.

#### Scenario: Operator reads network setup

- **WHEN** an operator reads the README's network instructions
- **THEN** they can configure access and understand its reach, credential rotation, and transport limits

## MODIFIED Requirements

### Requirement: A field keeps one notice

The system SHALL hold each field's last notice and answer it to clients authorized by the deployment's access mode.
A notice SHALL be a JSON object, and a second notice SHALL replace the first whole rather than merge.
A field SHALL keep a notice of its own, no field reading another's.

#### Scenario: A notice is written and read back

- **GIVEN** a field cora offers and an authorized client
- **WHEN** a notice is written to it and then asked for
- **THEN** what was written is answered

#### Scenario: A second notice

- **GIVEN** a field holding a notice naming two things
- **WHEN** an authorized client writes a notice naming one of them
- **THEN** what is answered is the second notice alone

#### Scenario: One field's notice is not another's

- **GIVEN** two fields cora offers, each written a notice of its own
- **WHEN** an authorized client asks for each
- **THEN** each answers what was written to it
