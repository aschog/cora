from cora.ports.host import Host
from fixture_plugins import identity


def extend(cora: Host) -> None:
    cora.register_tool(
        name="two",
        description="The two tool.",
        parameter_schema={"type": "integr", "properties": []},
        run=identity,
    )
