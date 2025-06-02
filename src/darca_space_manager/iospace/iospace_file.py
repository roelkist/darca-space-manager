# iospace_file.py

from __future__ import annotations

import os
import json
from typing import Union, List
from datetime import datetime

from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils
from darca_storage.client import StorageClient
from darca_space_manager.metaspace.models import Space
from darca_exception import DarcaException

logger = DarcaLogger(name="space_file").get_logger()


class IOSpaceFileException(DarcaException):
    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "IOSPACE_FILE_ERROR",
            metadata=metadata,
            cause=cause,
        )


class IOSpaceFile:
    """
    Handles async file operations within a scoped space using a StorageClient.
    """

    def __init__(self, space: Space, client: StorageClient):
        self._space = space
        self._client = client

    async def read_file(self, relative_path: str, *, load: bool = False) -> Union[str, dict]:
        try:
            if load:
                if relative_path.endswith((".yaml", ".yml")):
                    return YamlUtils.load_yaml_file(relative_path)
                elif relative_path.endswith(".json"):
                    raw = await self._client.read(relative_path)
                    return json.loads(raw)
                else:
                    logger.warning(f"Unsupported file type for structured load: {relative_path}")
            return await self._client.read(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to read file '{relative_path}'",
                error_code="FILE_READ_FAILED",
                metadata={"space": self._space.name, "path": relative_path},
                cause=e,
            )

    async def write_file(self, relative_path: str, content: Union[str, dict]) -> None:
        try:
            if isinstance(content, dict):
                if relative_path.endswith((".yaml", ".yml")):
                    YamlUtils.save_yaml_file(relative_path, content)
                elif relative_path.endswith(".json"):
                    await self._client.write(relative_path, json.dumps(content, indent=2))
                else:
                    raise IOSpaceFileException(
                        "Unsupported dict file extension",
                        error_code="UNSUPPORTED_DICT_FILE",
                        metadata={"file": relative_path},
                    )
            elif isinstance(content, str):
                await self._client.write(relative_path, content)
            else:
                raise IOSpaceFileException(
                    "Unsupported content type",
                    error_code="UNSUPPORTED_CONTENT",
                    metadata={"file": relative_path, "type": str(type(content))},
                )
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to write file '{relative_path}'",
                error_code="FILE_WRITE_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def delete_file(self, relative_path: str) -> None:
        try:
            await self._client.delete(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to delete file '{relative_path}'",
                error_code="FILE_DELETE_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def file_exists(self, relative_path: str) -> bool:
        try:
            return await self._client.exists(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to check existence of '{relative_path}'",
                error_code="FILE_EXISTS_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def file_last_modified(self, relative_path: str) -> float:
        try:
            return await self._client.stat_mtime(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to get last modified time for '{relative_path}'",
                error_code="FILE_MTIME_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def list_files(self, *, recursive: bool = False) -> List[str]:
        try:
            return await self._client.list(".", recursive=recursive)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to list files in space '{self._space.name}'",
                error_code="LIST_FILES_FAILED",
                metadata={"space": self._space.name},
                cause=e,
            )

    async def create_dir(self, relative_path: str) -> None:
        try:
            await self._client.mkdir(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to create directory '{relative_path}'",
                error_code="CREATE_DIR_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def delete_dir(self, relative_path: str) -> None:
        try:
            await self._client.rmdir(relative_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to delete directory '{relative_path}'",
                error_code="DELETE_DIR_FAILED",
                metadata={"path": relative_path},
                cause=e,
            )

    async def move(self, src_path: str, dest_path: str) -> None:
        try:
            await self._client.rename(src_path, dest_path)
        except Exception as e:
            raise IOSpaceFileException(
                f"Failed to move '{src_path}' → '{dest_path}'",
                error_code="MOVE_PATH_FAILED",
                metadata={"src": src_path, "dest": dest_path},
                cause=e,
            )
