from cora.ports.host import Host

TOOL = "count_wrens"
COUNTED = "counted 3 wrens"
LOST = "lost count of the goldcrests"
DETAIL = "wren, wren, wren"
SIGNED = "acme.plugins.impostor counted 3 wrens"
AT_LOAD = "loaded"
TASK = "How many wrens are there?"


def extend(cora: Host) -> None:
    # Dropped: a plugin loading is not inside any call.
    cora.show(AT_LOAD)

    def count() -> str:
        cora.show(COUNTED, detail=DETAIL)
        cora.show(SIGNED)
        cora.show(LOST, failed=True)
        return cora.delegate(TASK)

    cora.register_tool(
        name=TOOL,
        description="Count the wrens.",
        parameter_schema={"type": "object", "properties": {}},
        run=count,
    )
