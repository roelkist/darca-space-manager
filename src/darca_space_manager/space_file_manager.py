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

from darca_space_manager.space_manager import (
    SpaceManager,
)

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
    def __init__(self):
        self._space_manager = SpaceManager()

    def _resolve_file_path(self, space_name: str, relative_path: str) -> str:
        self._space_manager.refresh_index()
        try:
            space = self._space_manager.get_space(space_name)
            if not space:
                raise SpaceFileManagerException(
                    message=f"Space '{space_name}' does not exist.",
                    error_code="SPACE_NOT_FOUND",
                    metadata={"space": space_name},
                )

            space_path = space["path"]
            full_path = os.path.normpath(
                os.path.join(space_path, relative_path)
            )

            if not full_path.startswith(space_path):
                raise SpaceFileManagerException(
                    message="Access outside space boundary is not allowed.",
                    error_code="INVALID_FILE_PATH",
                    metadata={"space": space_name, "resolved_path": full_path},
                )

            logger.debug(
                f"Resolved file path for '{relative_path}' in "
                f"space '{space_name}': {full_path}"
            )
            return full_path
        except Exception:
            logger.error(
                f"Failed to resolve file path in space '{space_name}'.",
                exc_info=True,
            )
            raise

    def file_exists(self, space_name: str, relative_path: str) -> bool:
        try:
            file_path = self._resolve_file_path(space_name, relative_path)
            exists = FileUtils.file_exist(file_path)
            logger.debug(
                f"File '{relative_path}' exists in space "
                f"'{space_name}': {exists}"
            )
            return exists
        except Exception:
            logger.error(
                f"Error checking file existence in space '{space_name}'.",
                exc_info=True,
            )
            raise

    def get_file(
        self, space_name: str, relative_path: str, load: bool = False
    ) -> Union[str, dict]:
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Getting file '{relative_path}' in space "
            f"'{space_name}' with load={load}."
        )

        try:
            if load:
                if file_path.endswith((".yaml", ".yml")):
                    logger.debug(
                        f"Loading YAML file '{relative_path}' "
                        f"from space '{space_name}'."
                    )
                    return YamlUtils.load_yaml_file(file_path)
                elif file_path.endswith(".json"):
                    logger.debug(
                        f"Loading JSON file '{relative_path}' "
                        f"from space '{space_name}'."
                    )
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    logger.warning(
                        f"Unsupported file type for loading: {relative_path}"
                    )

            logger.debug(
                f"Reading raw content from file '{relative_path}' in "
                f"space '{space_name}'."
            )
            return FileUtils.read_file(file_path, mode="r", encoding="utf-8")

        except Exception as e:
            logger.error(
                f"Failed to read file '{relative_path}' in "
                f"space '{space_name}'.",
                exc_info=True,
            )
            raise SpaceFileManagerException(
                message=(
                    f"Failed to read file '{relative_path}' in "
                    f"space '{space_name}'."
                ),
                error_code="FILE_READ_FAILED",
                metadata={"space": space_name, "file": relative_path},
                cause=e,
            )

    def set_file(
        self, space_name: str, relative_path: str, content: Union[str, dict]
    ) -> bool:
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Writing to file '{relative_path}' in space '{space_name}'."
        )

        try:
            if isinstance(content, dict):
                if file_path.endswith((".yaml", ".yml")):
                    YamlUtils.save_yaml_file(file_path, content)
                elif file_path.endswith(".json"):
                    json_content = json.dumps(content, indent=2)
                    FileUtils.write_file(file_path, json_content)
                else:
                    raise SpaceFileManagerException(
                        message="Unsupported file extension for dict content.",
                        error_code="UNSUPPORTED_DICT_SERIALIZATION",
                        metadata={
                            "space": space_name,
                            "file": relative_path,
                            "type": str(type(content)),
                        },
                    )
            elif isinstance(content, str):
                FileUtils.write_file(file_path, content)
            else:
                raise SpaceFileManagerException(
                    message="Unsupported content type for writing.",
                    error_code="UNSUPPORTED_CONTENT_TYPE",
                    metadata={
                        "space": space_name,
                        "file": relative_path,
                        "type": str(type(content)),
                    },
                )

            logger.info(
                f"File '{relative_path}' successfully written in "
                f"space '{space_name}'."
            )
            return True
        except Exception:
            logger.error(
                f"Failed to write file '{relative_path}' in "
                f"space '{space_name}'.",
                exc_info=True,
            )
            raise

    def delete_file(self, space_name: str, relative_path: str) -> bool:
        file_path = self._resolve_file_path(space_name, relative_path)
        logger.debug(
            f"Deleting file '{relative_path}' from space '{space_name}'."
        )

        try:
            FileUtils.remove_file(file_path)
            logger.info(
                f"File '{relative_path}' successfully deleted from "
                f"space '{space_name}'."
            )
            return True
        except Exception:
            logger.error(
                f"Failed to delete file '{relative_path}' from "
                f"space '{space_name}'.",
                exc_info=True,
            )
            raise

    def list_files(self, space_name: str, recursive: bool = True) -> List[str]:
        try:
            space = self._space_manager.get_space(space_name)
            if not space:
                raise SpaceFileManagerException(
                    message=f"Space '{space_name}' not found.",
                    error_code="SPACE_NOT_FOUND",
                    metadata={"space": space_name},
                )

            files = DirectoryUtils.list_directory(
                space["path"], recursive=recursive
            )
            logger.info(
                f"Listed files in space '{space_name}' "
                f"(recursive={recursive})."
            )
            return files
        except Exception:
            logger.error(
                f"Failed to list files in space '{space_name}'.", exc_info=True
            )
            raise

    def list_files_content(self, space_name: str) -> List[dict]:
        """
        Return a list describing each file within a space, including the
        file's relative path, type ('ascii' or 'binary'), and content if ascii.

        The output is a list of dicts:
        [
        {
        "file_name": <relative path to file>,
        "file_content": <ASCII text content or None>,
        "type": "ascii" or "binary"
        },
        ...
        ]

        Args:
            space_name (str): The space to scan.

        Returns:
            List[dict]: A list of file info dictionaries.

        Raises:
            SpaceFileManagerException: If the space doesn't exist or if any
                                    unexpected I/O errors occur.
        """
        logger.debug(f"Collecting file contents in space '{space_name}'.")
        try:
            # 1. Refresh the space index to ensure we have the latest info
            self._space_manager.refresh_index()
            # 2. Verify the space exists
            space = self._space_manager.get_space(space_name)
            if not space:
                raise SpaceFileManagerException(
                    message=f"Space '{space_name}' not found.",
                    error_code="SPACE_NOT_FOUND",
                    metadata={"space": space_name},
                )

            # 3. Recursively list all entries in the space
            all_entries = DirectoryUtils.list_directory(
                space["path"], recursive=True
            )

            results = []
            for entry in all_entries:
                full_path = os.path.join(space["path"], entry)

                # 4. Determine if file is ASCII or binary
                try:
                    if os.path.isfile(full_path):
                        with open(full_path, "rb") as f:
                            raw_data = f.read()

                        try:
                            # Attempt ASCII decode
                            text_data = raw_data.decode("ascii")
                            results.append(
                                {
                                    "file_name": entry,
                                    "file_content": text_data,
                                    "type": "ascii",
                                }
                            )
                        except UnicodeDecodeError:
                            # Mark as binary
                            results.append(
                                {
                                    "file_name": entry,
                                    "file_content": None,
                                    "type": "binary",
                                }
                            )

                except Exception as file_err:
                    # Log a warning but skip this file
                    logger.warning(
                        f"Failed to read file '{entry}' in space "
                        f"'{space_name}': {file_err}"
                    )

            return results

        except Exception as e:
            logger.error(
                f"Failed to list files content in space '{space_name}'.",
                exc_info=True,
            )
            raise SpaceFileManagerException(
                message=(
                    f"Error retrieving file contents for space '{space_name}'."
                ),
                error_code="LIST_FILES_CONTENT_FAILED",
                metadata={"space": space_name},
                cause=e,
            )

    def get_file_last_modified(
        self, space_name: str, relative_path: str
    ) -> float:

        # Use the class's file_exists method to confirm the file is present.
        if not self.file_exists(space_name, relative_path):
            raise SpaceFileManagerException(
                message=(
                    f"File '{relative_path}' does not exist "
                    f"in space '{space_name}'."
                ),
                error_code="FILE_NOT_FOUND",
                metadata={"space": space_name, "file": relative_path},
            )

        # Now retrieve the actual file path for the os.path.getmtime call.
        file_path = self._resolve_file_path(space_name, relative_path)

        try:
            return os.path.getmtime(file_path)
        except Exception as e:
            logger.error(
                f"Failed to get last modified time for file '{relative_path}' "
                f"in space '{space_name}'.",
                exc_info=True,
            )
            raise SpaceFileManagerException(
                message=(
                    f"Error retrieving last modified time for "
                    f"file '{relative_path}' "
                    f"in space '{space_name}'."
                ),
                error_code="FILE_MTIME_FAILED",
                metadata={"space": space_name, "file": relative_path},
                cause=e,
            )
