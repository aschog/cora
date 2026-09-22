from dataclasses import replace

from cora.ports.host import BRIEFING, CALLING, RETURNING, Host
from cora.ports.plugin import ToolCall, ToolResult

MOTTO = "Open every answer with 'per the manifest'."
SHIPPING = "shipping"
LOOKUP = "lookup"
RAN = "the shipping tool ran"
NO_SHIPPING = "shipping is closed to plugins today"
SEALED = "sealed: {}"
ORDER = {
    "type": "object",
    "properties": {"order": {"type": "string"}},
    "required": ["order"],
}


def shipping(order: str) -> str:
    return RAN


def lookup(order: str) -> str:
    return f"{order} is three boxes"


def _motto(brief: str) -> str:
    return f"{brief}\n\n{MOTTO}"


def _refuse_shipping(call: ToolCall) -> str | None:
    return NO_SHIPPING if call.name == SHIPPING else None


def _seal(result: ToolResult) -> ToolResult | None:
    if result.error is not None:
        return None
    return replace(result, payload=SEALED.format(result.render()))


def extend(cora: Host) -> None:
    cora.register_tool(
        name=SHIPPING,
        description="Ship one order.",
        parameter_schema=ORDER,
        run=shipping,
    )
    cora.register_tool(
        name=LOOKUP,
        description="Look one order up.",
        parameter_schema=ORDER,
        run=lookup,
    )
    cora.register_handler(event=BRIEFING, handle=_motto)
    cora.register_handler(event=CALLING, handle=_refuse_shipping)
    cora.register_handler(event=RETURNING, handle=_seal)
