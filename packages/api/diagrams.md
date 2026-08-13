# Diagrams

## The classes, read off the source

```mermaid
classDiagram
  namespace domain {
    class AgentState
    class Chunk
    class Citable
    class Context
    class CoreError
    class MetadataFilter
    class QueryPlan
    class Source
    class TraceStep
  }
  namespace ports {
    class ChatModel
    class ContextSource
    class Embedder
    class Fact
    class GraphFor
    class GraphRunner
    class Loader
    class Memory
    class Message
    class ModelReply
    class Plugin
    class RetrievedChunk
    class Retriever
    class Step
    class Tool
    class ToolCall
    class ToolRefusal
    class ToolResult
    class ValidationRule
  }
  AgentState --> "*" Message
  AgentState --> "*" Source
  AgentState --> "*" TraceStep
  ChatModel ..> "*" Message
  ChatModel ..> "1" ModelReply
  ChatModel ..> "*" Tool
  Citable ..> "1" Context
  Citable ..> "*" Source
  Context --> "*" Source
  ContextSource ..> "*" RetrievedChunk
  GraphFor ..> "1" AgentState
  GraphFor ..> "1" GraphRunner
  GraphFor ..> "1" Step
  GraphRunner ..> "*" AgentState
  Memory ..> "*" Fact
  Message --> "*" ToolCall
  ModelReply --> "*" ToolCall
  Plugin --> "*" Tool
  Plugin --> "*" ValidationRule
  QueryPlan --> "0..1" MetadataFilter
  RetrievedChunk --> "1" Chunk
  Retriever ..> "*" Chunk
  Retriever ..> "0..1" MetadataFilter
  Retriever ..> "*" RetrievedChunk
  Step ..> "1" AgentState
```
