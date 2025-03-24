"""
space_file_manager.py

Provides file-level operations within managed logical spaces.
Supports reading, writing, deleting, and listing files within spaces,
with automatic handling of YAML/JSON content types.
"""

import json
import os
from typing import List, Union

from darca_exception.exception import DarcaException
from darca_file_utils.directory_utils import DirectoryUtils
from darca_file_utils.file_utils import FileUtils
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils

from darca_space_manager.space_manager import SpaceManager

# Initialize logger
logger = DarcaLogger(name="space_file_manager").get_logger()


class SpaceFileManagerException(DarcaException):
    """Custom exception for errors in the SpaceFileManager."""

    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "SPACE_FILE_MANAGER_ERROR",
            metadata=metadata,
            cause=cause,
        )


class SpaceFileManager:
    """
    Manages file-level operations within a logical space.
    """

    def __init__(self):
        self._space_manager = SpaceManager()

    def _resolve_file_path(self, space_name: str, relative_path: str) -> str:
        if not self._space_manager.space_exists(space_name):
            raise SpaceFileManagerException(
                message=f"Space '{space_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": space_name},
            )
        full_path = os.path.normpath(
            os.path.join(
                self._space_manager._get_space_path(space_name), relative_path
            )
        )
        base_path = self._space_manager._get_space_path(space_name)
        if not full_path.startswith(base_path):
            raise SpaceFileManagerException(
                message=(
                    f"Attempted to access outside of "
                    f"space boundary: {relative_path}"
                ),
                error_code="INVALID_FILE_PATH",
                metadata={"space": space_name, "resolved_path": full_path},
            )
        return full_path

    def file_exists(self, space_name: str, relative_path: str) -> bool:
        file_path = self._resolve_file_path(space_name, relative_path)
        return FileUtils.file_exist(file_path)

    def get_file(self, space_name: str, relative_path: str) -> str:
        """
        Get the ASCII content of a file. Returns raw text even
        for YAML/JSON files.

        Args:
            space_name (str): Name of the space.
            relative_path (str): Path relative to the space root.

        Returns:
            str: The file content as ASCII text.

        Raises:
            SpaceFileManagerException
        """
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Reading file '{relative_path}' in space '{space_name}' as text."
        )

        try:
            return FileUtils.read_file(file_path, mode="r", encoding="ascii")
        except Exception as e:
            raise SpaceFileManagerException(
                message=(
                    f"Failed to read file '{relative_path}' "
                    f"in space '{space_name}'."
                ),
                error_code="FILE_READ_FAILED",
                metadata={"space": space_name, "file": relative_path},
                cause=e,
            )

    def set_file(
        self, space_name: str, relative_path: str, content: Union[str, dict]
    ) -> bool:
        """
        Write content to a file inside a space.
        Automatically serializes dicts to YAML or JSON based on extension.

        Args:
            space_name (str): Name of the space.
            relative_path (str): Path relative to the space root.
            content (Union[str, dict]): Content to write.

        Returns:
            bool: True if successful.

        Raises:
            SpaceFileManagerException
        """
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Writing file '{relative_path}' in space '{space_name}'."
        )

        try:
            if isinstance(content, dict):
                if file_path.endswith((".yaml", ".yml")):
                    YamlUtils.save_yaml_file(file_path=file_path, data=content)
                elif file_path.endswith(".json"):
                    json_content = json.dumps(content, indent=2)
                    FileUtils.write_file(
                        file_path=file_path, content=json_content
                    )
                else:
                    raise SpaceFileManagerException(
                        message="Unsupported file extension for dict content.",
                        error_code="UNSUPPORTED_DICT_SERIALIZATION",
                        metadata={
                            "file": relative_path,
                            "space": space_name,
                            "type": str(type(content)),
                        },
                    )
            elif isinstance(content, str):
                FileUtils.write_file(file_path=file_path, content=content)
            else:
                raise SpaceFileManagerException(
                    message="Unsupported content type for writing.",
                    error_code="UNSUPPORTED_CONTENT_TYPE",
                    metadata={
                        "type": str(type(content)),
                        "file": relative_path,
                        "space": space_name,
                    },
                )
            return True
        except SpaceFileManagerException:
            raise  # Let specific exceptions bubble up
        except Exception as e:
            raise SpaceFileManagerException(
                message=(
                    f"Failed to write file '{relative_path}' "
                    f"in space '{space_name}'."
                ),
                error_code="FILE_WRITE_FAILED",
                metadata={"space": space_name, "file": relative_path},
                cause=e,
            )

    def delete_file(self, space_name: str, relative_path: str) -> bool:
        """
        Delete a file in a space.

        Args:
            space_name (str): Name of the space.
            relative_path (str): Path relative to the space root.

        Returns:
            bool: True if successful.

        Raises:
            SpaceFileManagerException
        """
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Deleting file '{relative_path}' in space '{space_name}'."
        )

        try:
            return FileUtils.remove_file(file_path)
        except Exception as e:
            raise SpaceFileManagerException(
                message=(
                    f"Failed to delete file '{relative_path}' "
                    f"in space '{space_name}'."
                ),
                error_code="FILE_DELETE_FAILED",
                metadata={"space": space_name, "file": relative_path},
                cause=e,
            )

    def list_files(self, space_name: str, recursive: bool = True) -> List[str]:
        """
        List files in a space.

        Args:
            space_name (str): Name of the space.
            recursive (bool): Whether to list files recursively.

        Returns:
            List[str]: List of file paths (relative to space root).

        Raises:
            SpaceFileManagerException
        """
        logger.debug(
            f"Listing files in space '{space_name}' (recursive={recursive})"
        )

        try:
            space_root = self._space_manager._get_space_path(space_name)
            return DirectoryUtils.list_directory(
                space_root, recursive=recursive
            )
        except Exception as e:
            raise SpaceFileManagerException(
                message=f"Failed to list files in space '{space_name}'.",
                error_code="LIST_FILES_FAILED",
                metadata={"space": space_name, "recursive": recursive},
                cause=e,
            )
