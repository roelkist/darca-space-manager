"""
api/space_file_manager.py

File-level operations within logical spaces.
Supports read, write, delete and list operations, with support for YAML/JSON and space URI addressing.
"""

import json
import os
import datetime
from typing import List, Union, Optional

from darca_exception.exception import DarcaException
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils

from .space_manager import SpaceManager
from darca_space_manager.metaspace.models import SpaceURI

logger = DarcaLogger(name="space_file_manager").get_logger()


class SpaceFileManagerException(DarcaException):
    """
    Custom exception for file operations inside spaces.
    """

    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "SPACE_FILE_MANAGER_ERROR",
            metadata=metadata,
            cause=cause,
        )


class SpaceFileManager:
    """
    Provides file-level operations within managed spaces.
    """

    def __init__(self, space_manager: SpaceManager):
        self._space_manager = space_manager
        self._backend = space_manager._backend

    def file_exists(self, path, user: Optional[str] = None) -> bool:
        exists = self._backend.exists(path)

        logger.debug(f"✅ File exists check: {path} → {exists}")
        return exists

    def get_file(self, file_path, load: bool = False, user: Optional[str] = None) -> Union[str, dict]:
        logger.debug(f"📥 Getting file: {file_path} (load={load})")

        try:
            if load:
                if file_path.endswith((".yaml", ".yml")):
                    return YamlUtils.load_yaml_file(file_path)
                elif file_path.endswith(".json"):
                    return json.loads(self._backend.read(file_path))
                else:
                    logger.warning(f"Unsupported file type for load: {file_path}")

            return self._backend.read(file_path)

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to read file '{file_path}'",
                error_code="FILE_READ_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def set_file(self, file_path, content: Union[str, dict], user: Optional[str] = None) -> bool:
        logger.debug(f"📥 Writing file: {file_path}")

        try:
            if isinstance(content, dict):
                if file_path.endswith((".yaml", ".yml")):
                    YamlUtils.save_yaml_file(file_path, content)
                elif file_path.endswith(".json"):
                    self._backend.write(file_path, json.dumps(content, indent=2))
                else:
                    raise SpaceFileManagerException(
                        "Unsupported dict file extension",
                        error_code="UNSUPPORTED_DICT_FILE",
                        metadata={"file": file_path},
                    )
            elif isinstance(content, str):
                self._backend.write(file_path, content)
            else:
                raise SpaceFileManagerException(
                    "Unsupported content type",
                    error_code="UNSUPPORTED_CONTENT",
                    metadata={"file": file_path, "type": str(type(content))},
                )

            logger.info(f"✅ File written: {file_path}")
            return True

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to write file '{file_path}'",
                error_code="FILE_WRITE_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def delete_file(self, file_path, user: Optional[str] = None) -> bool:
        logger.debug(f"🗑️ Deleting file: {file_path}")

        try:
            self._backend.delete(file_path)

            logger.info(f"✅ File deleted: {file_path}")
            return True

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to delete file '{file_path}'",
                error_code="FILE_DELETE_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def list_files(self, space_name: str, recursive: bool = False, files_only: bool = False, user: Optional[str] = None) -> List[str]:
        all_entries = self._backend.list(space_name, recursive=recursive)

        if files_only:
            return [
                entry for entry in all_entries
                if self.file_exists(SpaceURI(space=space_name, path=entry), user=user)
            ]
        return all_entries

    def list_files_content(self, space_name: str, user: Optional[str] = None) -> List[dict]:
        all_entries = self._backend.list(space_name, recursive=True)
        results = []

        for entry in all_entries:
            full_path = os.path.join(space_name, entry)
            try:
                raw_data = self._backend.read(full_path, binary=True)
                try:
                    text_data = raw_data.decode("ascii")
                    results.append({
                        "file_name": entry,
                        "file_content": text_data,
                        "type": "ascii",
                    })
                except UnicodeDecodeError:
                    results.append({
                        "file_name": entry,
                        "file_content": None,
                        "type": "binary",
                    })
            except Exception as e:
                logger.warning(f"⚠️ Failed to read file {entry}: {e}")

        return results

    def get_file_last_modified(self, file_path, user: Optional[str] = None) -> float:
        if not self.file_exists(file_path, user=user):
            raise SpaceFileManagerException(
                f"File '{file_path}' does not exist.",
                error_code="FILE_NOT_FOUND",
                metadata={"space_uri": str(file_path)},
            )
        
        try:
            return self._backend.stat_mtime(file_path)

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to get last modified time for file '{file_path}'",
                error_code="FILE_MTIME_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )
