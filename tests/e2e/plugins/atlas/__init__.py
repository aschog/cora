import pathlib

from cora.ports.host import Host

CONTRACT = 1
SCOPE = "atlas"


def extend(cora: Host) -> None:
    cora.register_instructions("You keep an atlas. Answer from it.", scope=SCOPE)
    cora.register_page(pathlib.Path(__file__).parent / "page", scope=SCOPE)
