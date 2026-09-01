"""Where a tool call is run, and what happens to it when it goes wrong."""

from dataclasses import dataclass, field

from jsonschema import Draft202012Validator, ValidationError

from cora.domain.errors import AdapterError
from cora.engine.plugin_set import Registry
from cora.engine.scoping import running_in
from cora.ports.plugin import Tool, ToolCall, ToolRefusal, ToolResult


@dataclass(frozen=True)
class ToolRuntime:
    """The tools a turn may call, and the one place a call is actually made.

    A tool's `ToolRefusal` is quoted; any other exception escaped rather than being
    written, so only its kind is passed on — its message could be carrying anything the
    tool was holding, and it reaches the model, the log and the user's trace alike.

    `tools` are cora's own, callable in every turn; `registry` holds what the plugins
    registered, and a turn reaches the ones its scopes apply to.
    """

    tools: tuple[Tool, ...]
    registry: Registry = field(default_factory=Registry)

    def execute(
        self, call: ToolCall, scopes: frozenset[str] = frozenset()
    ) -> ToolResult:
        """Run one call and answer for it, whatever happened.

        A tool nobody offers, arguments the schema refuses, a refusal, an unexpected
        exception, a tool that returned nothing — each comes back as a result carrying
        the reason, because the model is owed an answer for every call it made. A tool
        out of scope is a tool nobody offers, which is what putting one behind a scope
        means.

        The turn's scopes are bound for the length of the call, which is what makes
        every reader of the documents underneath it read one field: cora's own search,
        a plugin reading `Host.documents`, and a loop delegated from inside the call.

        Args:
            scopes: What the turn is running under, empty for a turn given none.

        Raises:
            AdapterError: Something outside cora failed. The one exception that
                propagates: a store that is unreachable will not be reachable for the
                next call either, so it ends the turn instead of being reported to the
                model as a bad call.
        """
        offered = (*self.tools, *self.registry.tools(scopes))
        tool = next((tool for tool in offered if tool.name == call.name), None)
        if tool is None:
            return ToolResult(call_id=call.call_id, error=f"unknown tool '{call.name}'")
        try:
            Draft202012Validator(tool.parameter_schema).validate(call.arguments)
        except ValidationError as exc:
            return ToolResult(
                call_id=call.call_id, error=f"invalid arguments: {exc.message}"
            )
        try:
            with running_in(scopes):
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
