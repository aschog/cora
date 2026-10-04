## 1. Outer Acceptance

- [x] 1.1 Write a strict-xfail outer test proving network startup blocks anonymous access while allowing authenticated API reads and mutations.

## 2. Startup Policy

- [x] 2.1 Write a test showing default startup serves loopback without credentials.
- [x] 2.2 Write a test showing explicit IPv4, IPv6, and localhost loopback bindings need no token.
- [x] 2.3 Write a test showing non-loopback addresses and hostnames refuse startup without explicit network opt-in.
- [x] 2.4 Write a test showing network mode refuses missing or blank API tokens before assembling the app.
- [x] 2.5 Write a test showing invalid network opt-in values refuse startup with a readable setting error.

## 3. HTTP Access

- [x] 3.1 Write a test showing missing credentials protect API data, mutations, plugin pages, uploads, field files, and static assets.
- [x] 3.2 Write a test showing malformed, incorrect, and unsupported authentication returns uniform `401` responses without changing app state.
- [x] 3.3 Write a test showing API clients using valid Basic credentials can perform normal reads and mutations.
- [ ] 3.4 Write a test showing valid Basic credentials unlock the page, its assets, plugin frames, and same-origin API requests.
- [ ] 3.5 Write a test showing network mode protects loopback-bound deployments too.
- [ ] 3.6 Write a test showing authenticated foreign-origin and null-origin uploads return `403` without keeping a document.
- [ ] 3.7 Write a test showing authenticated same-origin and originless clients can write notices.
- [ ] 3.8 Write a test showing authenticated answers stream normally and disconnecting still stops their turns.

## 4. Outer Green

- [ ] 4.1 Remove the strict-xfail marker and watch the network-access outer test pass.
