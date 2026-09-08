"""How every store of cora's own opens the one file they share."""

import pathlib
import sqlite3

BUSY_TIMEOUT_MS = 5000
"""How long a writer waits for the one ahead of it before giving up. Long enough that a
turn writing its own record never sees a busy store, short enough that a stuck one
surfaces as an error rather than a hang."""


def connect(path: str) -> sqlite3.Connection:
    """A connection onto the shared store, in the mode four writers need.

    Autocommit, because each store opens its own transactions where it needs one. Write
    ahead logging, because the default journal takes a lock that blocks readers for the
    length of a write, and this file has four writers and every reader of the page
    behind it. Both are the file's own state rather than the connection's, so they hold
    however the deployment opened it first.

    Args:
        path: The database file. Its directory is made if it is not there.

    Raises:
        sqlite3.Error: The file could not be opened. Each store translates that into
            the error its own port promises.
    """
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    connection.execute("pragma journal_mode = wal")
    connection.execute(f"pragma busy_timeout = {BUSY_TIMEOUT_MS}")
    return connection
