from cora.ports.host import Host


def extend(cora: Host) -> None:
    raise RuntimeError("the plugin fell over while registering")
