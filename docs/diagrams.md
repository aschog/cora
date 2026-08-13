# Diagrams

## The packages, read off the imports

```dot
digraph packages {
  graph [rankdir=BT, fontname=Helvetica, labeljust=l, labelloc=b, ranksep=0.7];
  node [shape=tab, fontname=Helvetica, margin=0.16];
  edge [fontname=Helvetica, fontsize=9, fontcolor=gray40, style=dashed, arrowhead=vee];
  subgraph cluster_cora {
    label="cora";
    labelloc=b;
    "cora.adapters" [label="adapters"];
    "cora.app" [label="app"];
    "cora.domain" [label="domain"];
    "cora.engine" [label="engine"];
    "cora.ports" [label="ports"];
    subgraph cluster_plugins {
      label="plugins";
      labelloc=b;
      "cora.plugins.fitness" [label="fitness"];
      "cora.plugins.security" [label="security"];
    }
    subgraph cluster_frontends {
      label="frontends";
      labelloc=b;
      "cora.frontends.streamlit" [label="streamlit"];
    }
  }
  "cora.adapters" -> "cora.domain" [label="«import»"];
  "cora.adapters" -> "cora.ports" [label="«import»"];
  "cora.app" -> "cora.adapters" [label="«import»"];
  "cora.app" -> "cora.domain" [label="«import»"];
  "cora.app" -> "cora.engine" [label="«import»"];
  "cora.app" -> "cora.ports" [label="«import»"];
  "cora.domain" -> "cora.ports" [label="«import»"];
  "cora.engine" -> "cora.domain" [label="«import»"];
  "cora.engine" -> "cora.ports" [label="«import»"];
  "cora.frontends.streamlit" -> "cora.app" [label="«import»"];
  "cora.frontends.streamlit" -> "cora.domain" [label="«import»"];
  "cora.frontends.streamlit" -> "cora.engine" [label="«import»"];
  "cora.frontends.streamlit" -> "cora.ports" [label="«import»"];
  "cora.plugins.fitness" -> "cora.domain" [label="«import»"];
  "cora.plugins.fitness" -> "cora.ports" [label="«import»"];
  "cora.plugins.security" -> "cora.domain" [label="«import»"];
  "cora.plugins.security" -> "cora.ports" [label="«import»"];
  "cora.ports" -> "cora.domain" [label="«import»"];
}
```

`make diagram` draws this into `packages.svg` beside this page — open that for the laid-out picture. It is not committed; graphviz draws it again whenever you ask.

## One turn

```mermaid
sequenceDiagram
  User->>Agent: answer("How does BM25 handle term saturation?")
  Agent->>GraphRunner: run(dict, "turn-diagram")
  GraphRunner-->>Agent: generator
  GraphRunner->>PrepareStep: (dict)
  PrepareStep->>Memory: recall()
  Memory-->>PrepareStep: 1 Fact
  GraphRunner->>ModelStep: (dict)
  ModelStep->>ChatModel: complete(2 Messages, 5 Tools)
  ChatModel-->>ModelStep: ModelReply
  GraphRunner->>Router: (dict)
  Router-->>GraphRunner: "tools"
  GraphRunner->>ToolStep: (dict)
  KnowledgeBase->>Embedder: embed(1 str)
  Embedder-->>KnowledgeBase: 1 list
  KnowledgeBase->>Retriever: query(16 floats, 5, None)
  Retriever-->>KnowledgeBase: 1 RetrievedChunk
  GraphRunner->>ModelStep: (dict)
  ModelStep->>ChatModel: complete(4 Messages, 5 Tools)
  ChatModel-->>ModelStep: ModelReply
  GraphRunner->>Router: (dict)
  Router-->>GraphRunner: "done"
  Agent-->>User: BM25 damps repeated terms [1].
```
