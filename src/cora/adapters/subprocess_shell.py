import os
import signal
import subprocess
from contextlib import suppress
from pathlib import Path

from cora.adapters.translating import translating
from cora.domain.errors import FieldFileError, FileNameRejectedError
from cora.ports.files import plain_name
from cora.ports.shell import Ran

MOST_OUTPUT = 20_000
MOST_SECONDS = 30.0

_translate_errors = translating(OSError, FieldFileError)


class SubprocessShell:
    """One shell per deployment, run in the directory of whichever field asks.

    The same root the field's files live under, so the model's command sees the files
    its read and write tools see. The root bounds the working directory and nothing
    more: what a command does from there is the command's, which the field tools say
    when they refuse a path that leaves.
    """

    def __init__(
        self, root: Path, cap: int = MOST_OUTPUT, seconds: float = MOST_SECONDS
    ) -> None:
        self._root = root
        self._cap = cap
        self._seconds = seconds

    @classmethod
    def at(
        cls, path: str, cap: int = MOST_OUTPUT, seconds: float = MOST_SECONDS
    ) -> "SubprocessShell":
        return cls(Path(path), cap, seconds)

    @_translate_errors
    def run(self, scope: str, command: str) -> Ran:
        if not plain_name(scope):
            raise FileNameRejectedError(scope)
        folder = self._root / scope
        folder.mkdir(parents=True, exist_ok=True)
        # Its own session, so what is stopped is the whole group and not the shell
        # alone: a command that backgrounds a child leaves that child holding the pipe,
        # and reading a pipe nobody is going to close outlives any timeout.
        running = subprocess.Popen(
            ["bash", "-c", command],
            cwd=folder,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            start_new_session=True,
        )
        try:
            printed, _ = running.communicate(timeout=self._seconds)
        except subprocess.TimeoutExpired as late:
            self._stop(running)
            output, cut = self._cut(_text(late.stdout))
            return Ran(output=output, cut=cut, stopped=True)
        output, cut = self._cut(printed)
        return Ran(output=output, code=running.returncode, cut=cut)

    def _stop(self, running: "subprocess.Popen[str]") -> None:
        # The whole group by the leader's own pid, which `start_new_session` makes the
        # group's: reading it back would fail where the shell has already exited and
        # left the child that holds the pipe still running, which is this case exactly.
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(running.pid, signal.SIGKILL)
        with suppress(subprocess.TimeoutExpired):
            running.wait(timeout=self._seconds)

    def _cut(self, output: str) -> tuple[str, bool]:
        if len(output) <= self._cap:
            return output, False
        return output[: self._cap], True


def _text(streamed: str | bytes | None) -> str:
    if streamed is None:
        return ""
    return streamed if isinstance(streamed, str) else streamed.decode(errors="replace")
