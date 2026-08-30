from cora.ports.host import Host
from fixture_plugins import make_tool

ONE = make_tool("one")


def extend(cora: Host) -> None:
    for _ in range(2):
        cora.register_tool(
            name=ONE.name,
            description=ONE.description,
            parameter_schema=ONE.parameter_schema,
            run=ONE.run,
        )
