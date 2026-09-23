from cora.ports.host import Host

CONTRACT = 1


def extend(cora: Host) -> None:
    cora.register_instructions("Written to the first contract.")
