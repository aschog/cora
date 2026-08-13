from cora.domain.trace import ModelDecision, ToolUse, TraceStep

HEADING = "One turn"
QUESTION = "How does BM25 handle term saturation?"
DOCUMENT = ("bm25.txt", b"BM25 saturates term frequency so repeats stop helping.")


def _arguments(step: ToolUse) -> str:
    return ", ".join(f'{name}="{value}"' for name, value in step.arguments.items())


def sequence(question: str, answer: str, trace: tuple[TraceStep, ...]) -> str:
    lines = ["sequenceDiagram", f"  User->>Agent: {question}"]
    for step in trace:
        if isinstance(step, ModelDecision):
            lines += [
                "  Agent->>ChatModel: complete()",
                f"  ChatModel-->>Agent: {step.summary}",
            ]
        elif isinstance(step, ToolUse):
            lines += [
                f"  Agent->>{step.name}: {_arguments(step)}",
                f"  {step.name}-->>Agent: {step.outcome}",
            ]
    return "\n".join([*lines, f"  Agent-->>User: {answer}"])


def render() -> str:
    from app_builder import assembled, indexed
    from cora.ports.chat_model import ModelReply
    from cora.ports.plugin import ToolCall
    from fakes import ScriptedChatModel, add_tool
    from fixture_plugins import make_plugin

    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name="search_documents",
                        arguments={"query": "term saturation"},
                        call_id="1",
                    ),
                )
            ),
            ModelReply(text="BM25 damps repeated terms [1]."),
        ]
    )
    app = indexed(
        assembled(chat_model=model, plugin=make_plugin(tools=(add_tool(),))), DOCUMENT
    )
    result = app.agent.answer(QUESTION, thread_id="turn-diagram")
    return sequence(QUESTION, result.answer, result.trace)
