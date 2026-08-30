from cora.ports.host import Host


def extend(cora: Host) -> None:
    cora.register_tool(
        name="   ",
        description="A tool nobody can name.",
        parameter_schema={"type": "object", "properties": {}},
        run=lambda: "ran",
    )
