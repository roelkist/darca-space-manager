# tests/test_space_executor.py

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
