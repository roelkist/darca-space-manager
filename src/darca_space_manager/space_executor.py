"""
space_executor.py

Allows executing commands *within* a given space directory using the darca-executor.
"""

import os
from typing import List, Union, Optional, Dict

from darca_exception.exception import DarcaException
from darca_log_facility.logger import DarcaLogger
from darca_executor import DarcaExecutor, DarcaExecError

from darca_space_manager.space_manager import SpaceManager


logger = DarcaLogger(name="space_executor").get_logger()


class SpaceExecutorException(DarcaException):
    """
    Custom exception for errors within the SpaceExecutor.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SPACE_EXECUTOR_ERROR",
        metadata: Optional[Dict] = None,
        cause: Exception = None,
    ):
        super().__init__(message=message, error_code=error_code, metadata=metadata, cause=cause)


class SpaceExecutor:
    """
    Encapsulates the logic for running commands within a managed space
    using the darca-executor module.
    """

    def __init__(self, use_shell: bool = False):
        """
        Initialize the SpaceExecutor with a DarcaExecutor and a SpaceManager.

        Args:
            use_shell (bool): Whether to run commands through the shell.
        """
        self._space_manager = SpaceManager()
        self._executor = DarcaExecutor(use_shell=use_shell)
        logger.debug(f"SpaceExecutor initialized (use_shell={use_shell}).")

    def run_in_space(
        self,
        space_name: str,
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
    ) -> "DarcaExecutor.CompletedProcess":
        """
        Run a command within the specified space directory using DarcaExecutor.

        Args:
            space_name (str): Name of the managed space.
            command (List[str] | str): The command to execute. Must be a list if use_shell=False,
                                       or a string if use_shell=True.
            capture_output (bool): If True, captures stdout/stderr.
            check (bool): Raise an exception if the command exits with a non-zero code.
            env (Optional[dict]): Environment variables to pass to the subprocess.
            timeout (Optional[int]): Timeout in seconds.

        Returns:
            subprocess.CompletedProcess: The result of the subprocess execution.

        Raises:
            SpaceExecutorException: If the space is not found, or if execution fails for any reason.
        """
        # 1. Resolve the space path
        self._space_manager.refresh_index()
        space = self._space_manager.get_space(space_name)
        if not space:
            logger.error(f"Space '{space_name}' not found.")
            raise SpaceExecutorException(
                message=f"Space '{space_name}' does not exist.",
                metadata={"space": space_name},
            )

        space_path = space["path"]
        logger.debug(f"Resolved space '{space_name}' to path: {space_path}")

        # 2. Invoke DarcaExecutor
        try:
            logger.debug("Executing command in space: %s", space_name)
            result = self._executor.run(
                command=command,
                capture_output=capture_output,
                check=check,
                cwd=space_path,
                env=env,
                timeout=timeout,
            )
            logger.info(
                "Command '%s' in space '%s' completed with returncode %d",
                command,
                space_name,
                result.returncode,
            )
            return result

        except DarcaExecError as e:
            # DarcaExecError is already quite detailed; wrap it for consistency
            logger.error("Command execution failed in space '%s'.", space_name, exc_info=True)
            raise SpaceExecutorException(
                message=f"Failed to run command in space '{space_name}'.",
                metadata={
                    "space": space_name,
                    "command": e.metadata.get("command"),
                    "returncode": e.metadata.get("returncode"),
                    "stdout": e.metadata.get("stdout"),
                    "stderr": e.metadata.get("stderr"),
                },
                cause=e,
            )
        except Exception as e:
            logger.error(
                "Unexpected error while running command in space '%s'.",
                space_name,
                exc_info=True,
            )
            raise SpaceExecutorException(
                message=f"Unexpected error while running command in space '{space_name}'.",
                metadata={"space": space_name, "command": command},
                cause=e,
            )
