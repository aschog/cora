from dataclasses import dataclass

from cora.core.citations import Source, cited_sources
from cora.core.ports.graph import GraphRunner
from cora.core.ports.plugin import ToolResult
from cora.core.turn import Turn


@dataclass(frozen=True)
class ChatResult:
    answer: str
    sources: tuple[Source, ...] = ()
    tool_results: tuple[ToolResult, ...] = ()


@dataclass(frozen=True)
class Agent:
    runner: GraphRunner

    def answer(self, question: str, history: tuple[Turn, ...] = ()) -> ChatResult:
        final = self.runner.run({"question": question, "history": history})
        answer = final.get("answer", "")
        return ChatResult(
            answer=answer,
            sources=cited_sources(answer, tuple(final.get("sources", ()))),
            tool_results=tuple(final.get("tool_results", ())),
        )
