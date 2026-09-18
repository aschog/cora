"""The plugin the browser suite runs its page against: one field, and a page for it.

A plugin of its own rather than a page added to `kit`, whose field three other specs
pin: a page changes the shape of the whole screen, and lending one to that field would
change the layout every one of them runs under.
"""

import pathlib

from cora.ports.host import Host

CONTRACT = 1
SCOPE = "atlas"


def extend(cora: Host) -> None:
    cora.register_instructions("You keep an atlas. Answer from it.", scope=SCOPE)
    cora.register_page(pathlib.Path(__file__).parent / "page", scope=SCOPE)
