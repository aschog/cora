"""Where a tool call is run, and what happens to it when it goes wrong."""

from dataclasses import dataclass

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.errors import AdapterError
from cora.ports.plugin import Tool, ToolCall, ToolRefusal, ToolResult


@dataclass(frozen=True)
class ToolRuntime:
    """The tools a turn may call, and the one place a call is actually made.

    A tool's `ToolRefusal` is quoted; any other exception escaped rather than being
    written, so only its kind is passed on — its message could be carrying anything the
    tool was holding, and it reaches the model, the log and the user's trace alike.
    """

    tools: tuple[Tool, ...]

    def execute(self, call: ToolCall) -> ToolResult:
        """Run one call and answer for it, whatever happened.

        A tool nobody offers, arguments the schema refuses, a refusal, an unexpected
        exception, a tool that returned nothing — each comes back as a result carrying
        the reason, because the model is owed an answer for every call it made.

        Raises:
            AdapterError: Something outside cora failed. The one exception that
                propagates: a store that is unreachable will not be reachable for the
                next call either, so it ends the turn instead of being reported to the
                model as a bad call.
        """
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
        except ToolRefusal as refused:
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
