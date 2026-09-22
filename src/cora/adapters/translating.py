"""One decorator every adapter translates its technology's failures through.

Each adapter owes its port the same thing — nothing from a library reaches a shell, and
the original is kept as the cause for the log — and each was writing the same nine lines
to owe it. What differs between them is a caught tuple and a class, so those are what
this takes.
"""

from collections.abc import Callable
from functools import wraps

from cora.domain.errors import AdapterError

type Caught = type[Exception] | tuple[type[Exception], ...]


def translating[**P, R](
    caught: Caught, into: type[AdapterError]
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Turn whatever `caught` names into `into`, with the original as its cause.

    Args:
        caught: The technology's own exceptions, as `except` takes them.
        into: The category the port promises. It takes no message: the class is the
            message, so one category reads alike everywhere it is raised.
    """

    def decorator(method: Callable[P, R]) -> Callable[P, R]:
        @wraps(method)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return method(*args, **kwargs)
            except caught as error:
                raise into() from error

        return wrapper

    return decorator
