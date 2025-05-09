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
from darca_file_utils.directory_utils import DirectoryUtils
from darca_file_utils.file_utils import FileUtils
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils

from darca_space_manager.api.space_manager import SpaceManager
from darca_space_manager.models.space_uri import SpaceURI
from darca_space_manager.core.space_path_manager import SpacePathManager
from darca_space_manager.models.space import Space

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

    def __init__(self, space_manager: Optional[SpaceManager] = None):
        self._space_manager = space_manager or SpaceManager()

    def _resolve_file_path(self, space_uri: SpaceURI) -> str:
        space = self._space_manager.get_space(space_uri.space_name)
        if not space:
            raise SpaceFileManagerException(
                message=f"Space '{space_uri.space_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": space_uri.space_name},
            )

        return SpacePathManager().resolve_path(space.path, space_uri.relative_path)

    def _touch_space_metadata(self, space_name: str):
        """
        Update the last_modified_at of the space metadata.
        """
        space = self._space_manager.get_space(space_name)
        if not space:
            raise SpaceFileManagerException(
                message=f"Space '{space_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": space_name},
            )

        updated_space = Space(
            name=space.name,
            path=space.path,
            label=space.label,
            parent=space.parent,
            created_at=space.created_at,
            last_modified_at=datetime.datetime.now(datetime.timezone.utc),
        )

        self._space_manager._registry.add_space(updated_space.name, updated_space.to_dict())
        logger.debug(f"📌 Space '{space_name}' metadata touched (last_modified_at updated).")

    def file_exists(self, uri: Union[str, SpaceURI]) -> bool:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        file_path = self._resolve_file_path(uri)
        exists = FileUtils.file_exist(file_path)

        logger.debug(f"✅ File exists check: {file_path} → {exists}")
        return exists

    def get_file(self, uri: Union[str, SpaceURI], load: bool = False) -> Union[str, dict]:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        file_path = self._resolve_file_path(uri)

        logger.debug(f"📥 Getting file: {file_path} (load={load})")

        try:
            if load:
                if file_path.endswith((".yaml", ".yml")):
                    return YamlUtils.load_yaml_file(file_path)
                elif file_path.endswith(".json"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    logger.warning(f"Unsupported file type for load: {file_path}")

            return FileUtils.read_file(file_path, mode="r", encoding="utf-8")

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to read file '{file_path}'",
                error_code="FILE_READ_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def set_file(self, uri: Union[str, SpaceURI], content: Union[str, dict]) -> bool:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        file_path = self._resolve_file_path(uri)

        logger.debug(f"📥 Writing file: {file_path}")

        try:
            if isinstance(content, dict):
                if file_path.endswith((".yaml", ".yml")):
                    YamlUtils.save_yaml_file(file_path, content)
                elif file_path.endswith(".json"):
                    FileUtils.write_file(file_path, json.dumps(content, indent=2))
                else:
                    raise SpaceFileManagerException(
                        "Unsupported dict file extension",
                        error_code="UNSUPPORTED_DICT_FILE",
                        metadata={"file": file_path},
                    )
            elif isinstance(content, str):
                FileUtils.write_file(file_path, content)
            else:
                raise SpaceFileManagerException(
                    "Unsupported content type",
                    error_code="UNSUPPORTED_CONTENT",
                    metadata={"file": file_path, "type": str(type(content))},
                )

            self._touch_space_metadata(uri.space_name)

            logger.info(f"✅ File written: {file_path}")
            return True

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to write file '{file_path}'",
                error_code="FILE_WRITE_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def delete_file(self, uri: Union[str, SpaceURI]) -> bool:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        file_path = self._resolve_file_path(uri)

        logger.debug(f"🗑️ Deleting file: {file_path}")

        try:
            FileUtils.remove_file(file_path)

            self._touch_space_metadata(uri.space_name)

            logger.info(f"✅ File deleted: {file_path}")
            return True

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to delete file '{file_path}'",
                error_code="FILE_DELETE_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )

    def list_files(self, space_name: str, recursive: bool = False, files_only: bool = False) -> List[str]:
        space = self._space_manager.get_space(space_name)
        if not space:
            raise SpaceFileManagerException(
                message=f"Space '{space_name}' not found.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": space_name},
            )

        all_entries = DirectoryUtils.list_directory(space.path, recursive=recursive)

        if files_only:
            return [entry for entry in all_entries if self.file_exists(SpaceURI(space_name=space_name, relative_path=entry))]
        else:
            return all_entries

    def list_files_content(self, space_name: str) -> List[dict]:
        space = self._space_manager.get_space(space_name)
        if not space:
            raise SpaceFileManagerException(
                message=f"Space '{space_name}' not found.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": space_name},
            )

        logger.debug(f"📦 Collecting file contents for space: {space_name}")

        all_entries = DirectoryUtils.list_directory(space.path, recursive=True)
        results = []

        for entry in all_entries:
            full_path = os.path.join(space.path, entry)

            if os.path.isfile(full_path):
                try:
                    with open(full_path, "rb") as f:
                        raw_data = f.read()

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

    def get_file_last_modified(self, uri: Union[str, SpaceURI]) -> float:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        if not self.file_exists(uri):
            raise SpaceFileManagerException(
                f"File '{uri}' does not exist.",
                error_code="FILE_NOT_FOUND",
                metadata={"space_uri": str(uri)},
            )

        file_path = self._resolve_file_path(uri)

        try:
            return os.path.getmtime(file_path)

        except Exception as e:
            raise SpaceFileManagerException(
                f"Failed to get last modified time for file '{file_path}'",
                error_code="FILE_MTIME_FAILED",
                metadata={"space_uri": str(uri)},
                cause=e,
            )
