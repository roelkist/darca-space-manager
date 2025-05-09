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

from darca_space_manager.api.space_manager import SpaceManager
from darca_space_manager.models.space_uri import SpaceURI
from darca_space_manager.core.space_path_manager import SpacePathManager

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

    def __init__(self, space_manager: Optional[SpaceManager] = None, use_shell: bool = False):
        self._space_manager = space_manager or SpaceManager()
        self._executor = DarcaExecutor(use_shell=use_shell)
        logger.debug(f"SpaceExecutor initialized (use_shell={use_shell}).")

    def run_in_space(
        self,
        uri: Union[str, SpaceURI],
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
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

        Returns:
            CompletedProcess: The result of execution.

        Raises:
            SpaceExecutorException: On failures.
        """
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        space = self._space_manager.get_space(uri.space_name)
        if not space:
            logger.error(f"❌ Space '{uri.space_name}' not found.")
            raise SpaceExecutorException(
                message=f"Space '{uri.space_name}' does not exist.",
                metadata={"space": uri.space_name},
            )

        try:
            resolved_cwd = SpacePathManager().resolve_path(space.path, uri.relative_path)

            logger.debug(f"📌 Running command in space '{uri.space_name}' at '{resolved_cwd}': {command}")

            result = self._executor.run(
                command=command,
                capture_output=capture_output,
                check=check,
                cwd=resolved_cwd,
                env=env,
                timeout=timeout,
            )

            logger.info(
                f"✅ Command '{command}' executed in space '{uri.space_name}' with return code {result.returncode}"
            )

            return result

        except DarcaExecError as e:
            logger.error(f"❌ Command execution failed in space '{uri.space_name}'.", exc_info=True)
            raise SpaceExecutorException(
                message=f"Command failed in space '{uri.space_name}'.",
                metadata={
                    "space": uri.space_name,
                    "command": e.metadata.get("command"),
                    "returncode": e.metadata.get("returncode"),
                    "stdout": e.metadata.get("stdout"),
                    "stderr": e.metadata.get("stderr"),
                },
                cause=e,
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error while running command in space '{uri.space_name}'.", exc_info=True)
            raise SpaceExecutorException(
                message=f"Unexpected error running command in space '{uri.space_name}'.",
                metadata={"space": uri.space_name, "command": command},
                cause=e,
            )
