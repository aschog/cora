from dataclasses import dataclass

from jsonschema import Draft202012Validator, ValidationError

from cora.core.errors import AdapterError
from cora.core.ports.plugin import Tool, ToolCall, ToolResult


@dataclass(frozen=True)
class ToolRuntime:
    """A tool refuses its input by raising `ValueError`, and that message is
    quoted: the tool wrote it for whoever reads it. Any other exception escaped
    rather than being written, so only its kind is passed on — the message could
    be carrying anything the tool was holding, and it travels to the model, the
    log and the user's trace alike."""

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
        except AdapterError:
            raise
        except ValueError as refused:
            return ToolResult(
                call_id=call.call_id, error=f"tool '{call.name}' failed: {refused}"
            )
        except Exception as exc:
            return ToolResult(
                call_id=call.call_id,
                error=f"tool '{call.name}' failed: {type(exc).__name__}",
            )
        if payload is None:
            return ToolResult(
                call_id=call.call_id, error=f"tool '{call.name}' returned no result"
            )
        return ToolResult(call_id=call.call_id, payload=payload)
