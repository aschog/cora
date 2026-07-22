from dataclasses import dataclass

from jsonschema import Draft202012Validator, ValidationError

from docchat.plugin import Tool, ToolCall, ToolResult


@dataclass
class ToolRuntime:
    tools: tuple[Tool, ...]

    def execute(self, call: ToolCall) -> ToolResult:
        tool = next((tool for tool in self.tools if tool.name == call.name), None)
        if tool is None:
            return ToolResult(call_id=call.call_id, error=f"unknown tool '{call.name}'")
        try:
            Draft202012Validator(tool.parameter_schema).validate(call.arguments)
        except ValidationError as exc:
            return ToolResult(
                call_id=call.call_id, error=f"invalid arguments: {exc.message}"
            )
        try:
            payload = tool.run(**call.arguments)
        except Exception as exc:
            return ToolResult(
                call_id=call.call_id, error=f"tool '{call.name}' failed: {exc}"
            )
        return ToolResult(call_id=call.call_id, payload=payload)
