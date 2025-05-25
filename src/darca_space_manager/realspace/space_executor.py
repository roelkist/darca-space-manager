"""
api/space_executor.py

Encapsulates logic for running commands within managed logical spaces.
Supports safe command execution with space boundary enforcement and URI addressing.
"""

import os
from typing import Dict, List, Optional, Union

from darca_exception import DarcaException
from darca_executor import DarcaExecError, DarcaExecutor
from darca_log_facility import DarcaLogger
from darca_storage.interfaces.file_backend import FileBackend

from .space_manager import SpaceManager
from darca_space_manager.metaspace.models import SpaceURI
from darca_space_manager.realspace.space_path_service import SpacePathService

logger = DarcaLogger(name="space_executor").get_logger()


class SpaceExecutorException(DarcaException):
    """
    Custom exception for errors during space command execution.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "SPACE_EXECUTOR_ERROR",
        metadata: Optional[Dict] = None,
        cause: Exception = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            metadata=metadata,
            cause=cause,
        )


class SpaceExecutor:
    """
    Executes commands inside logical spaces using darca-executor.
    Enforces space boundaries and supports SpaceURI addressing.
    """

    def __init__(
        self,
        space_manager: SpaceManager,
        use_shell: bool = False
    ):
        self._space_manager = space_manager or SpaceManager()
        self._executor = DarcaExecutor(use_shell=use_shell)
        self._backend = space_manager._backend
        logger.debug(f"SpaceExecutor initialized (use_shell={use_shell}).")

    def run_in_space(
        self,
        space: str,
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
        user: Optional[str] = None,
    ) -> "DarcaExecutor.CompletedProcess":
        """
        Run a command within the specified space using DarcaExecutor.

        Args:
            uri (str | SpaceURI): Space URI or SpaceURI object.
            command (List[str] | str): Command to execute.
            capture_output (bool): Capture stdout/stderr.
            check (bool): Raise error if command fails.
            env (Optional[dict]): Environment variables.
            timeout (Optional[int]): Timeout in seconds.
            user (Optional[str]): User identity for access control.

        Returns:
            CompletedProcess: The result of execution.

        Raises:
            SpaceExecutorException: On failures.
        """
        # Access control check
        try:
            self._space_manager._assert_access(space, user)
        except Exception as e:
            raise SpaceExecutorException(
                message=str(e),
                error_code="EXEC_ACCESS_DENIED",
                metadata={"space": space, "user": user},
                cause=e,
            )

        try:
            if not self._backend.exists(space):
                raise SpaceExecutorException(
                    message=f"Resolved path '{space}' does not exist in space '{space}'.",
                    metadata={"space": space, "path": space},
                )

            logger.debug(f"📌 Running command in space '{space}' at '{space}': {command}")

            result = self._executor.run(
                command=command,
                capture_output=capture_output,
                check=check,
                cwd=space,
                env=env,
                timeout=timeout,
            )

            logger.info(
                f"✅ Command '{command}' executed in space '{space}' with return code {result.returncode}"
            )

            return result

        except DarcaExecError as e:
            logger.error(f"❌ Command execution failed in space '{space}'.", exc_info=True)
            raise SpaceExecutorException(
                message=f"Command failed in space '{space}'.",
                metadata={
                    "space": space,
                    "command": e.metadata.get("command"),
                    "returncode": e.metadata.get("returncode"),
                    "stdout": e.metadata.get("stdout"),
                    "stderr": e.metadata.get("stderr"),
                },
                cause=e,
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error while running command in space '{space}'.", exc_info=True)
            raise SpaceExecutorException(
                message=f"Unexpected error running command in space '{space}'.",
                metadata={"space": space, "command": command},
                cause=e,
            )
