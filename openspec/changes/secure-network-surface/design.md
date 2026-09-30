## Context

The React frontend owns HTTP startup, static serving, streaming routes, and the watch's unauthenticated notice endpoint.

## Goals / Non-Goals

- Keep deployment access policy outside the app, engine, domain, and plugin contract.
- Preserve route payloads, streaming cancellation, live plugin loading, and default local usage.
- Exclude user accounts, a login screen, persistent sessions, rate limiting, and built-in TLS termination.
- Leave loopback browser hardening beyond network mode to a separate story.

## Decisions

- Place a frontend-owned access policy at the startup and HTTP-dispatch seams.
- Parse host, port, network mode, and credentials before assembling models or opening stores.
- Recognize `localhost` and numeric loopback addresses locally, treating other names conservatively without DNS lookups.
- Enable authentication whenever network mode is selected, including deployments behind a loopback-bound reverse proxy.
- Compose pure ASGI middleware around the route surface, avoiding request buffering and streaming lifecycle changes.
- Keep the same middleware boundary available to in-process API tests without reading ambient environment variables.
- Model credentials as grants, with full-access and single-notice grants implementing one permission interface.
- Register authentication decoders for Bearer and Basic credentials rather than extending a scheme-selection switch.
- Accept Basic only for full API access, using username `cora` and the API token as its password.
- Challenge unauthorized requests with a stable Basic realm so browsers authenticate before loading any protected assets.
- Use constant-time secret comparison, uniform authentication errors, and no token-bearing response content or URLs.
- Apply the access gate before static serving, route lookup, app composition refresh, and request-body parsing.
- Match notice grants against the canonical request path and method, never prefixes or substring matches.
- Keep notice size, field existence, replacement, and timestamp validation in the existing route.
- Refuse identical full-access and watch credentials to prevent accidental privilege escalation.
- Reject foreign and null Origin headers on network-mode mutations, comparing against the request's effective origin.
- Allow authenticated native clients without Origin headers and authenticated same-origin browser mutations.
- Do not enable permissive CORS or trust forwarded headers from arbitrary clients.
- Generate ignored watch configuration through an environment-reading build helper rather than secret-bearing shell substitutions.
- Load optional `.env` settings through uv, letting explicit environment settings take precedence.
- Serialize configuration safely and send the watch token only through its Authorization header.
- Share the watch field setting between server authorization and extension generation to prevent mismatched notice grants.
- Make `run-watch` explicitly enable network mode while keeping its existing host and keep-awake wrapper.
- Preserve address and device overrides while replacing `WATCH_FIELD` with the shared `CORA_WATCH_SCOPE` setting.

## Boundaries and Guards

- No core ports, architecture maps, dependency declarations, or Telegram contracts change.
- Existing architecture guards continue enforcing frontend isolation and documented-name contracts.
- Watch build guards exercise generated configuration and captured output with fake external tooling.
- HTTP tests use real middleware, an assembled fake-backed app, and the public request surface.
- Startup tests substitute only server and assembly boundaries, checking served behavior instead of collaborator call counts.
- Browser acceptance includes manually opening the protected page, its plugin frame, and a streamed turn.
- Documentation acceptance is a human read, never a prose-matching test.

## Risks / Trade-offs

- Unencrypted HTTP reveals tokens in transit → recommend trusted networks or HTTPS termination before wider access.
- Browser-managed Basic credentials are ambient → enforce same-origin mutation checks in network mode.
- Basic login has no reliable logout control → document browser credential caching and restart-based server rotation.
- A watch package contains its credential → grant only one notice write and keep generated packages ignored.
- Native watch transport needs device verification → test delivery on the phone and wrist before merge.
- An API token grants shell-capable access → document that it is operator authority, not a multi-user boundary.
- Shared tokens lack per-user revocation → defer accounts and sessions rather than building an identity subsystem.
- TLS proxies change the visible scheme → document trusted proxy configuration and verify browser-origin matching before deployment.

## Migration Plan

- Keep existing local commands working without additional settings.
- Require operators using public bindings to add explicit network mode and an API token.
- Require watch operators to add a distinct watch token and rebuild their extension.
- Support loopback-only rollback by disabling network mode and restoring a loopback host.
