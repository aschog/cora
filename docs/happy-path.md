# What happens when you ask

## A document goes in

![A UML sequence diagram of an upload: cora.frontends calls add_file on the knowledge
base, which asks the retriever whether it holds these bytes already, and then either
repairs the text of an upload indexed before any text was kept, or ingests, embeds, keeps
and indexes it.](assets/upload-map.svg)

## A turn, as a frontend asks for one

![A UML sequence diagram of a turn: a frontend calls answer on the agent, the agent runs
the thread on the graph runner, reports each new step to the caller as the states arrive,
asks whether the turn stopped to ask, and records the turn before handing back a
ChatResult.](assets/turn-map.svg)

## A round, as the graph walks it

![A UML sequence diagram of one turn inside the graph: the runner takes the prepare step,
then loops over the model step and the router, and on the router's answer either runs the
round's tools, stops to put a decision to the reader before running them, or leaves the
loop with the answer.](assets/round-map.svg)

## The tool that reaches the documents

`ToolStep` never knows which tool it ran. It asks `ToolRuntime` for the name the model
gave, and hands back whatever came out — numbered `[n]` first if the result can cite
itself.

![A UML sequence diagram of a document search: the tool runtime runs the tool, which asks
its context source to search, and the knowledge base embeds the question with the same
embedder the chunks went through and reads the nearest chunks out of the
index.](assets/search-map.svg)
