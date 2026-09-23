"""Which field the work happening right now belongs to.

A tool call is the one place every reader of the documents passes through, and the
scopes a turn runs under are already there. Binding them for the length of the call is
what makes cora's own search, a plugin reading `Host.documents` and a delegated loop's
own search all read one field without any of them being handed it: a plugin cannot see
the turn it is running in, so a parameter would be a field nobody could fill.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from cora.domain.errors import UnsettledFieldError
from cora.ports.host import DEFAULT_SCOPE

_running_in: ContextVar[frozenset[str]] = ContextVar("_running_in", default=frozenset())


@contextmanager
def running_in(scopes: frozenset[str]) -> Iterator[None]:
    """Run this block in these fields, and leave the ones outside it as they were.

    Reset rather than cleared, so a delegated loop inside a call does not take the
    turn's own field away from the call that follows it.
    """
    token = _running_in.set(scopes)
    try:
        yield
    finally:
        _running_in.reset(token)


def here() -> frozenset[str]:
    """The fields the work happening now belongs to, the default one where none was set.

    Never empty: a search always has somewhere to look, and a bare cora looks in the
    field that is what a bare cora is.
    """
    return _running_in.get() or frozenset({DEFAULT_SCOPE})


def the_field() -> str:
    """The one field the work happening now belongs to.

    What a file is read from or written into: a plugin's files and cora's own three
    tools both go through here, so both refuse the same way when the turn runs in more
    than one field and no single directory is meant.

    Raises:
        UnsettledFieldError: The work is running in several fields at once.
    """
    fields = here()
    if len(fields) != 1:
        raise UnsettledFieldError(fields)
    return next(iter(fields))
