import pytest

from cora.domain.errors import FileNameRejectedError
from cora.engine.field_tools import (
    BASH_DESCRIPTION,
    OUTPUT_CUT,
    STOPPED,
    bash_tool,
    read_tool,
    write_tool,
)
from cora.engine.scoping import running_in
from cora.engine.tool_runtime import ToolRuntime
from cora.ports.host import DEFAULT_SCOPE
from cora.ports.plugin import ToolCall, ToolRefusal
from cora.ports.shell import Ran
from fakes import FakeFiles, FakeShell


def test_the_read_tool_returns_the_fields_file_by_name() -> None:
    files = FakeFiles(
        {(DEFAULT_SCOPE, "note.md"): "maples", ("travel", "note.md"): "x"}
    )

    assert read_tool(files).run(name="note.md") == "maples"
    with running_in(frozenset({"travel"})):
        assert read_tool(files).run(name="note.md") == "x"


def test_a_name_nothing_was_kept_under_is_refused_as_not_there() -> None:
    with pytest.raises(ToolRefusal, match=r"note\.md"):
        read_tool(FakeFiles()).run(name="note.md")


def test_the_write_tool_keeps_text_under_a_name_the_field_then_lists() -> None:
    files = FakeFiles()

    said = write_tool(files).run(name="note.md", text="maples")

    assert files.read(DEFAULT_SCOPE, "note.md") == "maples"
    assert files.names(DEFAULT_SCOPE) == ("note.md",)
    assert "note.md" in said


@pytest.mark.parametrize("tool", [read_tool, write_tool])
def test_a_name_that_is_not_plain_is_refused_with_the_reason(tool) -> None:
    files = FakeFiles({(DEFAULT_SCOPE, "note.md"): "maples"})
    runtime = ToolRuntime(tools=(tool(files),))
    arguments = {"name": "../secrets.md", "text": "x"}
    if tool is read_tool:
        del arguments["text"]

    result = runtime.execute(
        ToolCall(name=tool(files).name, arguments=arguments, call_id="c1")
    )

    assert result.error is not None
    assert FileNameRejectedError("../secrets.md").user_message in result.error
    assert files.kept == {(DEFAULT_SCOPE, "note.md"): "maples"}


@pytest.mark.parametrize(
    "command", ["cat ../secrets.md", "ls /etc", "cat ~/.ssh/id_rsa", "cd .. && ls"]
)
def test_a_command_naming_a_path_outside_the_field_is_refused_unrun(
    command: str,
) -> None:
    shell = FakeShell()

    with pytest.raises(ToolRefusal, match="outside"):
        bash_tool(shell).run(command=command)

    assert shell.ran == []


def test_a_command_runs_in_the_turns_field_and_answers_with_its_output() -> None:
    shell = FakeShell([Ran(output="plan.md\n")])

    with running_in(frozenset({"fitness"})):
        said = bash_tool(shell).run(command="ls -la ./notes")

    assert shell.ran == [("fitness", "ls -la ./notes")]
    assert said == "plan.md\n"


def test_a_cut_or_stopped_command_says_so_under_its_output() -> None:
    cut = bash_tool(FakeShell([Ran(output="abc", cut=True)])).run(command="ls")
    stopped = bash_tool(FakeShell([Ran(output="", stopped=True)])).run(command="ls")
    failed = bash_tool(FakeShell([Ran(output="no such", code=2)])).run(command="ls")

    assert cut.startswith("abc\n") and OUTPUT_CUT in cut
    assert STOPPED in stopped
    assert "exit code 2" in failed


def test_a_file_that_is_not_text_is_refused_as_that_and_not_as_missing() -> None:
    files = FakeFiles({(DEFAULT_SCOPE, "scan.pdf"): b"\x89PNG\x00\xff"})

    with pytest.raises(ToolRefusal, match="not one that reads as text") as refused:
        read_tool(files).run(name="scan.pdf")

    assert "scan.pdf" in str(refused.value)
    assert "no file named" not in str(refused.value)


@pytest.mark.parametrize(
    "command",
    ["cat $HOME/.ssh/id_rsa", "cat ${HOME}/x", "cat ~georg/x", "ls $PWD/.."],
)
def test_a_command_naming_the_machine_rather_than_the_field_is_refused(
    command: str,
) -> None:
    shell = FakeShell()

    with pytest.raises(ToolRefusal, match="outside"):
        bash_tool(shell).run(command=command)

    assert shell.ran == []


@pytest.mark.parametrize(
    "command", ["ls notes/", "grep -r squat .", "wc -l *.md", "cat a.md b.md"]
)
def test_a_command_that_stays_in_the_field_runs(command: str) -> None:
    shell = FakeShell()

    bash_tool(shell).run(command=command)

    assert shell.ran == [(DEFAULT_SCOPE, command)]


def test_the_tool_does_not_tell_the_model_it_is_held_to_the_field() -> None:
    # It is an argument check over the command's text, and text is not a boundary: a
    # description promising one would be read as a guarantee that is not there.
    assert "refused" in BASH_DESCRIPTION
    assert "sandbox" in BASH_DESCRIPTION
