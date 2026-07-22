from dataclasses import dataclass

from docchat.plugin import Tool, ToolCall, ToolResult


@dataclass
class ToolRuntime:
    tools: tuple[Tool, ...]

    def execute(self, call: ToolCall) -> ToolResult:
        tool = next(tool for tool in self.tools if tool.name == call.name)
        return ToolResult(call_id=call.call_id, payload=tool.run(**call.arguments))
