# iospace_exec.py
# License: MIT

from typing import Union, Optional, List, Dict
from darca_storage.client import StorageClient
from darca_space_manager.metaspace.models import Space
from darca_executor import DarcaExecutor, DarcaExecError
from darca_log_facility.logger import DarcaLogger
from darca_exception import DarcaException

logger = DarcaLogger(name="space_exec").get_logger()


class IOSpaceExecException(DarcaException):
    def __init__(
        self,
        message: str,
        error_code: str = "IOSPACE_EXEC_ERROR",
        metadata: Optional[Dict] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message, error_code, metadata, cause)


class IOSpaceExec:
    """
    Executes commands inside the root of a space, safely jailed by StorageClient.
    """

    def __init__(self, space: Space, client: StorageClient):
        self._space = space
        self._client = client
        self._executor = DarcaExecutor()

    async def run(
        self,
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
        user: Optional[str] = None,
    ):
        """
        Run a command inside the space directory, jailed by the client.

        Args:
            command: Command string or argument list
            capture_output: Whether to capture stdout/stderr
            check: Raise error if return code non-zero
            env: Environment variables
            timeout: Max time to run
            user: Optional user context

        Returns:
            DarcaExecutor.CompletedProcess
        """
        try:
            logger.debug(f"🚀 Executing in space '{self._space.name}': {command}")

            cwd = await self._client.resolve_path(".")  # jailed space root

            result = self._executor.run(
                command=command,
                capture_output=capture_output,
                check=check,
                cwd=cwd,
                env=env,
                timeout=timeout,
            )

            logger.info(f"✅ Ran '{command}' in '{cwd}' with code {result.returncode}")
            return result

        except DarcaExecError as e:
            logger.error("❌ Execution failure", exc_info=True)
            raise IOSpaceExecException(
                message=f"Command failed in space '{self._space.name}'",
                metadata={
                    "space": self._space.name,
                    "command": e.metadata.get("command"),
                    "returncode": e.metadata.get("returncode"),
                    "stdout": e.metadata.get("stdout"),
                    "stderr": e.metadata.get("stderr"),
                },
                cause=e,
            )

        except Exception as e:
            logger.error("❌ Unexpected error during command execution", exc_info=True)
            raise IOSpaceExecException(
                message=f"Unexpected error running command in space '{self._space.name}'",
                metadata={"space": self._space.name, "command": command},
                cause=e,
            )
