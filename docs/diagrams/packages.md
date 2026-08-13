# The packages, read off the imports

One box per package, one arrow per boundary an import crosses. Nobody draws this page:
`make diagram` rewrites the block below from the source, and `tests/test_package_diagram.py`
fails when the committed one is stale — so it is the import graph as it is today, not as
someone last remembered it.

Read an arrow as *depends on*. The contract sits at the top, as it does in
[the distributions diagram](../big-picture.md#the-distributions) — but that one's arrows are
what each package **declares** in its manifest, and these are what its modules **import**. The
two differ on purpose: `cora` depends on `cora-plugin-security` to ship the guard its default
set names, and imports it nowhere.

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 40, "rankSpacing": 50, "curve": "basis"}}}%%
flowchart BT
  cora.adapters --> cora.domain
  cora.adapters --> cora.ports
  cora.app --> cora.adapters
  cora.app --> cora.domain
  cora.app --> cora.engine
  cora.app --> cora.ports
  cora.domain --> cora.ports
  cora.engine --> cora.domain
  cora.engine --> cora.ports
  cora.frontends.streamlit --> cora.app
  cora.frontends.streamlit --> cora.domain
  cora.frontends.streamlit --> cora.engine
  cora.frontends.streamlit --> cora.ports
  cora.plugins.fitness --> cora.domain
  cora.plugins.fitness --> cora.ports
  cora.plugins.security --> cora.domain
  cora.plugins.security --> cora.ports
  cora.ports --> cora.domain
```

`cora.domain` and `cora.ports` point at each other: the state a graph runner drives names the
model's message type, and the port that drives it names the state. Both ship in `cora-api`, so
the cycle costs no install anything — but it is in the source, so it is in the picture.

`cora.plugins` and `cora.frontends` are the two extension points, so their children are the
boxes and neither appears itself. A second frontend is a box here the day it is installed,
with no edit to the generator.
