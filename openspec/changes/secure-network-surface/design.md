## Context

The React frontend owns HTTP startup, static serving, streaming routes, and the currently unauthenticated notice endpoint.

## Goals / Non-Goals

- Keep deployment access policy outside the app, engine, domain, and plugin contract.
- Preserve route payloads, streaming cancellation, live plugin loading, and default local usage.
- Exclude user accounts, a login screen, persistent sessions, rate limiting, and built-in TLS termination.
- Leave loopback browser hardening beyond network mode to a separate story.
- Defer watch credentials, restricted grants, build changes, and device testing to the backlog.

## Decisions

- Place a frontend-owned access policy at the startup and HTTP-dispatch seams.
- Parse host, port, network mode, and credentials before assembling models or opening stores.
- Recognize `localhost` and numeric loopback addresses locally, treating other names conservatively without DNS lookups.
- Enable authentication whenever network mode is selected, including deployments behind a loopback-bound reverse proxy.
- Compose pure ASGI middleware around the route surface, avoiding request buffering and streaming lifecycle changes.
- Keep the same middleware boundary available to in-process API tests without reading ambient environment variables.
- Register authentication decoders for Bearer and Basic credentials rather than extending a scheme-selection switch.
- Authenticate both schemes against one operator token, using username `cora` for Basic access.
- Challenge unauthorized requests with a stable Basic realm so browsers authenticate before loading any protected assets.
- Use constant-time secret comparison, uniform authentication errors, and no token-bearing response content or URLs.
- Apply the access gate before static serving, route lookup, app composition refresh, and request-body parsing.
- Protect the notice endpoint like every other route, leaving its existing validation and payloads unchanged.
- Reject foreign and null Origin headers on network-mode mutations, comparing against the request's effective origin.
- Allow authenticated native clients without Origin headers and authenticated same-origin browser mutations.
- Do not enable permissive CORS or trust forwarded headers from arbitrary clients.
- Leave watch commands and extension code unchanged, without adding an unauthenticated compatibility exception.

## Boundaries and Guards

- No core ports, architecture maps, dependency declarations, or Telegram contracts change.
- Existing architecture guards continue enforcing frontend isolation and documented-name contracts.
- HTTP tests use real middleware, an assembled fake-backed app, and the public request surface.
- Startup tests substitute only server and assembly boundaries, checking served behavior instead of collaborator call counts.
- Browser acceptance includes manually opening the protected page, its plugin frame, and a streamed turn.
- Documentation acceptance is a human read, never a prose-matching test.

## Risks / Trade-offs

- Unencrypted HTTP reveals tokens in transit → recommend trusted networks or HTTPS termination before wider access.
- Browser-managed Basic credentials are ambient → enforce same-origin mutation checks in network mode.
- Basic login has no reliable logout control → document browser credential caching and restart-based server rotation.
- Existing watch requests lack credentials → document incompatibility and defer authenticated watch delivery to its own story.
- An API token grants shell-capable access → document that it is operator authority, not a multi-user boundary.
- Shared tokens lack per-user revocation → defer accounts and sessions rather than building an identity subsystem.
- TLS proxies change the visible scheme → document trusted proxy configuration and verify browser-origin matching before deployment.

## Migration Plan

- Keep existing local commands working without additional settings.
- Require operators using public bindings to add explicit network mode and an API token.
- Document that unchanged `run-watch` needs explicit network settings and its watch client cannot authenticate until follow-up support ships.
- Support loopback-only rollback by disabling network mode and restoring a loopback host.
