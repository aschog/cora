## 1. Outer Acceptance

- [ ] 1.1 Write a strict-xfail outer test proving network startup blocks anonymous access while accepting notice-only watch writes.

## 2. Startup Policy

- [ ] 2.1 Write a test showing default startup serves loopback without credentials.
- [ ] 2.2 Write a test showing explicit IPv4, IPv6, and localhost loopback bindings need no token.
- [ ] 2.3 Write a test showing non-loopback addresses and hostnames refuse startup without explicit network opt-in.
- [ ] 2.4 Write a test showing network mode refuses missing or blank API tokens before assembling the app.
- [ ] 2.5 Write a test showing invalid network opt-in values refuse startup with a readable setting error.
- [ ] 2.6 Write a test showing matching API and watch tokens refuse startup without disclosing credentials.
- [ ] 2.7 Write a test showing a watch field configured without its token refuses startup.

## 3. HTTP Access

- [ ] 3.1 Write a test showing missing credentials protect API data, mutations, plugin pages, uploads, field files, and static assets.
- [ ] 3.2 Write a test showing malformed and incorrect authentication returns uniform `401` responses without changing app state.
- [ ] 3.3 Write a test showing valid Bearer API credentials allow normal reads and mutations.
- [ ] 3.4 Write a test showing valid Basic credentials unlock the page, its assets, plugin frames, and same-origin API requests.
- [ ] 3.5 Write a test showing network mode protects loopback-bound deployments too.
- [ ] 3.6 Write a test showing authenticated foreign-origin and null-origin uploads return `403` without keeping a document.
- [ ] 3.7 Write a test showing authenticated same-origin and originless clients can write notices.
- [ ] 3.8 Write a test showing authenticated answers stream normally and disconnecting still stops their turns.

## 4. Notice-Only Grants

- [ ] 4.1 Write a test showing the watch token writes its configured field's notice, readable through API credentials.
- [ ] 4.2 Write a test showing watch credentials cannot read, mutate other routes, or write another field's notice.
- [ ] 4.3 Write a test showing encoded and near-matching notice paths cannot widen the watch credential's grant.
- [ ] 4.4 Write a test showing watch-authenticated notices retain existing field, size, object, replacement, and timestamp behavior.

## 5. Watch Delivery

- [ ] 5.1 Write a test showing `run-watch` enables authenticated network mode and preserves keep-awake behavior.
- [ ] 5.2 Write a test showing watch configuration uses environment credentials, the shared field, and existing address overrides.
- [ ] 5.3 Write a test showing watch configuration loads an ignored `.env` when credentials are absent from the environment.
- [ ] 5.4 Write a test showing watch builds refuse missing notice credentials without overwriting an existing configuration.
- [ ] 5.5 Write a test showing generated watch configuration remains ignored and build output contains neither token.
- [ ] 5.6 Write a test showing the watch sends its notice-only Bearer credential through an Authorization header.

## 6. Outer Green

- [ ] 6.1 Remove the strict-xfail marker and watch the network-access outer test pass.
