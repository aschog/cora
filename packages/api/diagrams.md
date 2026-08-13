# Diagrams

## The classes, read off the source

```dot
digraph classes {
  graph [rankdir=LR, fontname=Helvetica, labeljust=l, ranksep=1.1, pack=true];
  node [shape=box, fontname=Helvetica, margin=0.12];
  edge [fontname=Helvetica, fontsize=10, labelfontsize=9, labeldistance=2.6, arrowhead=vee];
  subgraph cluster_domain {
    label="domain";
    labeljust=l;
    AgentState [label=<AgentState>];
    Chunk [label=<Chunk>];
    Citable [label=<<I>Citable</I>>];
    Context [label=<Context>];
    CoreError [label=<CoreError>];
    MetadataFilter [label=<MetadataFilter>];
    QueryPlan [label=<QueryPlan>];
    Source [label=<Source>];
    TraceStep [label=<<I>TraceStep</I>>];
  }
  subgraph cluster_ports {
    label="ports";
    labeljust=l;
    ChatModel [label=<&#171;interface&#187;<BR/>ChatModel>];
    ContextSource [label=<&#171;interface&#187;<BR/>ContextSource>];
    Embedder [label=<&#171;interface&#187;<BR/>Embedder>];
    Fact [label=<Fact>];
    GraphFor [label=<&#171;interface&#187;<BR/>GraphFor>];
    GraphRunner [label=<&#171;interface&#187;<BR/>GraphRunner>];
    Loader [label=<&#171;interface&#187;<BR/>Loader>];
    Memory [label=<&#171;interface&#187;<BR/>Memory>];
    Message [label=<Message>];
    ModelReply [label=<ModelReply>];
    Plugin [label=<Plugin>];
    RetrievedChunk [label=<RetrievedChunk>];
    Retriever [label=<&#171;interface&#187;<BR/>Retriever>];
    Step [label=<&#171;interface&#187;<BR/>Step>];
    Tool [label=<Tool>];
    ToolCall [label=<ToolCall>];
    ToolRefusal [label=<ToolRefusal>];
    ToolResult [label=<ToolResult>];
    ValidationRule [label=<&#171;interface&#187;<BR/>ValidationRule>];
  }
  AgentState -> Message [headlabel="messages *"];
  AgentState -> Source [headlabel="sources *"];
  AgentState -> TraceStep [headlabel="trace *"];
  ChatModel -> Message [headlabel="*", style=dashed];
  ChatModel -> ModelReply [headlabel="1", style=dashed];
  ChatModel -> Tool [headlabel="*", style=dashed];
  Citable -> Context [headlabel="1", style=dashed];
  Citable -> Source [headlabel="*", style=dashed];
  Context -> Source [headlabel="sources *"];
  ContextSource -> RetrievedChunk [headlabel="*", style=dashed];
  GraphFor -> AgentState [headlabel="1", style=dashed];
  GraphFor -> GraphRunner [headlabel="1", style=dashed];
  GraphFor -> Step [headlabel="1", style=dashed];
  GraphRunner -> AgentState [headlabel="*", style=dashed];
  Memory -> Fact [headlabel="*", style=dashed];
  Message -> ToolCall [headlabel="tool_calls *"];
  ModelReply -> ToolCall [headlabel="tool_calls *"];
  Plugin -> Tool [headlabel="tools *"];
  Plugin -> ValidationRule [headlabel="validation_rules *"];
  QueryPlan -> MetadataFilter [headlabel="metadata_filter 0..1"];
  RetrievedChunk -> Chunk [headlabel="chunk 1"];
  Retriever -> Chunk [headlabel="*", style=dashed];
  Retriever -> MetadataFilter [headlabel="0..1", style=dashed];
  Retriever -> RetrievedChunk [headlabel="*", style=dashed];
  Step -> AgentState [headlabel="1", style=dashed];
}
```

`make diagram` draws this into `classes.svg` beside this page — open that for the laid-out picture. It is not committed; graphviz draws it again whenever you ask.
