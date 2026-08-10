from cora.core.agent_state import AgentState
from cora.core.citations import Source
from cora.core.ports.plugin import ToolResult
from cora.core.services.agent import Agent
from cora.core.turn import Turn


class _StubRunner:
    def __init__(self, final: AgentState) -> None:
        self.final = final
        self.seeded: AgentState | None = None

    def run(self, state: AgentState) -> AgentState:
        self.seeded = state
        return self.final


def test_answer_seeds_the_run_from_the_question_and_history() -> None:
    history = (Turn(role="user", text="I weigh 80 kg."),)
    runner = _StubRunner({"answer": "80 kg."})

    result = Agent(runner).answer("What was my weight?", history)

    assert runner.seeded == {"question": "What was my weight?", "history": history}
    assert result.answer == "80 kg."


def test_only_the_cited_sources_are_reported_under_their_own_numbers() -> None:
    registered = [Source(1, "a.md"), Source(2, "b.md"), Source(3, "c.md")]
    runner = _StubRunner({"answer": "Per [3] and [1].", "sources": registered})

    result = Agent(runner).answer("q")

    assert result.sources == (Source(1, "a.md"), Source(3, "c.md"))


def test_the_runs_tool_results_come_back_in_order() -> None:
    results = [
        ToolResult(call_id="c1", payload="passages"),
        ToolResult(call_id="c2", payload=42),
    ]
    runner = _StubRunner({"answer": "done", "tool_results": results})

    result = Agent(runner).answer("q")

    assert result.tool_results == tuple(results)
