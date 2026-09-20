"""How every store of cora's own opens the one file they share."""

import pathlib
import sqlite3


def connect(path: str) -> sqlite3.Connection:
    """A connection onto the shared store, in the mode five writers need.

    Autocommit, because each store opens its own transactions where it needs one. Write
    ahead logging, because the default journal takes a lock that blocks readers for the
    length of a write, and this file has five writers and every reader of the page
    behind it. That mode is the file's own state rather than the connection's, so it
    holds however the deployment opened it first. How long a contended writer waits is
    the connection's, and `sqlite3.connect` already installs its five seconds.

    Args:
        path: The database file. Its directory is made if it is not there.

    Raises:
        sqlite3.Error: The file could not be opened.
        OSError: Its directory could not be made. Each store translates both into the
            error its own port promises.
    """
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    connection.execute("pragma journal_mode = wal")
    return connection
