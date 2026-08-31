"""A plugin asking for a version of the contract cora does not offer."""

from cora.ports.host import Host

CONTRACT = 99


def extend(cora: Host) -> None:
    cora.register_instructions("You should never read this.")
