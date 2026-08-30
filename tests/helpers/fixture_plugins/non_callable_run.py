from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_tool(
        name="two",
        description="The two tool.",
        parameter_schema={"type": "object", "properties": {}},
        run="not callable",  # ty: ignore[invalid-argument-type]
    )
