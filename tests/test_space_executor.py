# tests/test_space_executor.py

import os
import subprocess
from unittest.mock import patch

import pytest

from darca_space_manager.space_executor import SpaceExecutorException


def test_run_in_space_non_existent_space(space_executor):
    """
    If the specified space does not exist, we expect a SpaceExecutorException.
    """
    with pytest.raises(SpaceExecutorException) as exc_info:
        space_executor.run_in_space("no_such_space", ["echo", "Hello"])
    assert "does not exist" in str(exc_info.value)
    assert "SPACE_EXECUTOR_ERROR" in str(exc_info.value)


def test_run_in_space_success(space_executor, space_manager):
    """
    Happy path: run a simple command in an existing space.
    """
    space_name = "executor_success_space"
    space_manager.create_space(space_name)

    # We'll run a basic command that should succeed. (ls .)
    result = space_executor.run_in_space(space_name, ["ls", "."])
    assert result.returncode == 0
    # 'capture_output' is True by default, so we have stdout/stderr
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)


def test_run_in_space_command_failure(space_executor, space_manager):
    """
    If the command fails (non-zero exit code), DarcaExecError is raised
    in DarcaExecutor,
    which is then caught and re-raised as SpaceExecutorException.
    """
    space_name = "executor_failure_space"
    space_manager.create_space(space_name)

    # Command that should fail with a non-zero exit code
    # (ls on a non-existent dir).
    with pytest.raises(SpaceExecutorException) as exc_info:
        space_executor.run_in_space(
            space_name, ["ls", "non_existent_directory"]
        )
    assert "Failed to run command in space" in str(exc_info.value)
    # We also expect the re-wrapped metadata,
    # including 'returncode', 'stdout', 'stderr'.


def test_run_in_space_unexpected_exception(space_executor, space_manager):
    """
    If an unexpected exception (not DarcaExecError) occurs in the 'try' block,
    we catch and raise SpaceExecutorException.
    """
    space_name = "executor_unexpected_space"
    space_manager.create_space(space_name)

    # Patch _executor.run to raise a random exception
    with patch.object(
        space_executor._executor, "run", side_effect=ValueError("Mocked error")
    ):
        with pytest.raises(SpaceExecutorException) as exc_info:
            space_executor.run_in_space(space_name, ["echo", "test"])
    assert "Unexpected error while running command in space" in str(
        exc_info.value
    )
    assert (
        "VALUEERROR" not in str(exc_info.value).upper()
    )  # It's re-wrapped, but you can check cause if needed


def test_run_in_space_with_cwd_success(space_executor, space_manager):
    """
    Create a space with a subdirectory. Then run a command in that subdirectory
    using the new 'cwd' argument to run_in_space.
    """
    space_name = "cwd_success_space"
    space_manager.create_space(space_name)
    space_path = space_manager.get_space(space_name)["path"]

    subdir = "subdir"
    os.makedirs(os.path.join(space_path, subdir), exist_ok=True)

    # We'll run a simple "ls" command in that subdir
    result = space_executor.run_in_space(
        space_name, command=["ls", "."], cwd=subdir, capture_output=True
    )
    assert result.returncode == 0
    # We can't precisely check the contents, but we know it executed in subdir
    # If subdir is empty, STDOUT might be blank
    assert isinstance(result.stdout, str)


def test_run_in_space_with_cwd_escape(space_executor, space_manager):
    """
    Attempt to specify a cwd that escapes the space boundary ('../outside').
    Should raise a SpaceExecutorException.
    """
    space_name = "cwd_escape_space"
    space_manager.create_space(space_name)

    with pytest.raises(SpaceExecutorException) as exc_info:
        space_executor.run_in_space(
            space_name,
            command=["ls", "."],
            cwd="../outside",
            capture_output=True,
        )
    assert "escapes space boundaries" in str(exc_info.value)


def test_run_in_space_with_cwd_no_subdir(space_executor, space_manager):
    """
    If the cwd subdirectory doesn't exist, the command might fail or succeed
    at the OS level. We only confirm it doesn't raise boundary check,
    and that we pass a valid path to the underlying executor.
    """
    space_name = "cwd_missing_subdir"
    space_manager.create_space(space_name)

    # Mock the DarcaExecutor.run call to return a dummy CompletedProcess
    with patch.object(space_executor._executor, "run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["ls", "."], returncode=0, stdout="mocked stdout", stderr=""
        )

        result = space_executor.run_in_space(
            space_name,
            command=["ls", "."],
            cwd="this_subdir_does_not_exist",
            capture_output=True,
        )

        # Confirm the final_cwd we pass to run(...) is joined with space path
        final_cwd = mock_run.call_args[1]["cwd"]
        assert final_cwd.endswith("this_subdir_does_not_exist")
        assert result.returncode == 0
        assert "mocked stdout" in result.stdout
