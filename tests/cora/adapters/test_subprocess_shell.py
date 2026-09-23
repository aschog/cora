import pathlib
import time

from cora.adapters.subprocess_shell import SubprocessShell


def test_a_command_runs_in_the_fields_own_directory(tmp_path: pathlib.Path) -> None:
    (tmp_path / "fitness").mkdir()
    (tmp_path / "fitness" / "plan.md").write_text("squats")
    (tmp_path / "travel").mkdir()
    (tmp_path / "travel" / "kyoto.md").write_text("maples")

    ran = SubprocessShell.at(str(tmp_path)).run("fitness", "ls")

    assert ran.output.split() == ["plan.md"]
    assert ran.code == 0


def test_a_field_with_no_directory_yet_gets_one(tmp_path: pathlib.Path) -> None:
    ran = SubprocessShell.at(str(tmp_path)).run("fitness", "pwd")

    assert (
        pathlib.Path(ran.output.strip()).resolve() == (tmp_path / "fitness").resolve()
    )
    assert (tmp_path / "fitness").is_dir()


def test_output_past_the_cap_is_cut_and_said_to_be(tmp_path: pathlib.Path) -> None:
    ran = SubprocessShell.at(str(tmp_path), cap=10).run(
        "f", "printf '%s' 0123456789abcdef"
    )

    assert (ran.output, ran.cut, ran.stopped) == ("0123456789", True, False)


def test_a_command_past_the_time_is_stopped_and_said_to_be(
    tmp_path: pathlib.Path,
) -> None:
    ran = SubprocessShell.at(str(tmp_path), seconds=0.2).run("f", "echo begun; sleep 5")

    assert ran.stopped is True
    assert ran.output.strip() == "begun"


def test_a_command_whose_child_holds_the_pipe_is_still_stopped(
    tmp_path: pathlib.Path,
) -> None:
    # A backgrounded child inherits the pipe, so waiting on the output outlives the
    # command cora stopped. The whole group goes, or the call never comes back.
    began = time.monotonic()

    ran = SubprocessShell.at(str(tmp_path), seconds=0.3).run(
        "f", "(sleep 30; echo late) & echo begun"
    )

    assert time.monotonic() - began < 10
    assert "begun" in ran.output


def test_a_command_stopped_past_the_cap_says_it_was_cut_as_well(
    tmp_path: pathlib.Path,
) -> None:
    ran = SubprocessShell.at(str(tmp_path), cap=5, seconds=0.3).run(
        "f", "printf '%s' 0123456789; sleep 30"
    )

    assert (ran.output, ran.cut, ran.stopped) == ("01234", True, True)
