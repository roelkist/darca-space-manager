"""
api/space_manager.py

High-level API for managing logical spaces.
"""

import datetime
import os
from typing import Dict, List, Optional

from darca_exception.exception import DarcaException
from darca_file_utils.directory_utils import DirectoryUtils
from darca_log_facility.logger import DarcaLogger

from darca_space_manager.core.space_registry import SpaceMetadataRegistry
from darca_space_manager.core.space_path_manager import SpacePathManager
from darca_space_manager.core.space_operation_lock import SpaceOperationLock
from darca_space_manager.models.space import Space

logger = DarcaLogger(name="space_manager").get_logger()


class SpaceManagerException(DarcaException):
    def __init__(self, message, error_code=None, metadata=None, cause=None):
        super().__init__(
            message=message,
            error_code=error_code or "SPACE_MANAGER_ERROR",
            metadata=metadata,
            cause=cause,
        )


class SpaceManager:
    """
    API layer for managing logical spaces.
    """

    def __init__(self):
        self._registry = SpaceMetadataRegistry()

    def space_exists(self, name: str) -> bool:
        return self._registry.get_space(name) is not None

    def get_space(self, name: str) -> Optional[Space]:
        data = self._registry.get_space(name)
        return Space.from_dict(data) if data else None

    def get_space_info(self, name: str) -> Space:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        latest_timestamp = self._compute_space_last_modified(space.path)
        space.last_modified_at = datetime.datetime.fromtimestamp(latest_timestamp, datetime.timezone.utc)
        return space

    def _compute_space_last_modified(self, path: str) -> float:
        all_entries = DirectoryUtils.list_directory(path, recursive=True)

        if not all_entries:
            return os.path.getmtime(path)

        latest_timestamp = 0.0

        for entry in all_entries:
            full_path = os.path.join(path, entry)

            if os.path.isfile(full_path):
                file_mtime = os.path.getmtime(full_path)
                if file_mtime > latest_timestamp:
                    latest_timestamp = file_mtime

        return latest_timestamp or os.path.getmtime(path)

    def create_space(
        self, name: str, label: str = "", parent_path: Optional[str] = None
    ) -> Space:
        if self.space_exists(name):
            raise SpaceManagerException(
                f"Space '{name}' already exists.",
                metadata={"space": name},
            )

        with SpaceOperationLock(name):
            try:
                if parent_path:
                    parts = parent_path.strip("/").split("/")
                    base_space_name = parts[0]
                    relative_subpath = os.path.join(*parts[1:]) if len(parts) > 1 else ""

                    base_space = self.get_space(base_space_name)
                    if not base_space:
                        raise SpaceManagerException(
                            f"Base space '{base_space_name}' not found.",
                            error_code="BASE_SPACE_NOT_FOUND",
                            metadata={"base": base_space_name, "path": parent_path},
                        )

                    base_path = base_space.path
                    destination_path = os.path.normpath(os.path.join(base_path, relative_subpath, name))

                    SpacePathManager().ensure_within_space(base_path, destination_path)

                    DirectoryUtils.create_directory(os.path.dirname(destination_path))
                else:
                    destination_path = os.path.join(
                        self._registry.load_registry().get("base_path", os.path.expanduser("~/.local/share/darca_space/spaces")),
                        name,
                    )

                DirectoryUtils.create_directory(destination_path)

                space = Space(
                    name=name,
                    label=label,
                    parent=parent_path,
                    path=destination_path,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    last_modified_at=datetime.datetime.now(datetime.timezone.utc),
                )

                self._registry.add_space(space.name, space.to_dict())

                logger.info(f"✅ Space '{name}' created at '{destination_path}' with label '{label}'.")

                return space

            except Exception as e:
                logger.error(f"❌ Failed to create space '{name}'.", exc_info=True)
                raise SpaceManagerException(
                    f"Failed to create space '{name}'.",
                    error_code="CREATE_SPACE_FAILED",
                    metadata={"space": name},
                    cause=e,
                )

    def delete_space(self, name: str) -> bool:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' not found.",
                metadata={"space": name},
            )

        with SpaceOperationLock(name):
            try:
                DirectoryUtils.remove_directory(space.path)
                self._registry.remove_space(name)

                logger.info(f"🗑️ Space '{name}' deleted.")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to delete space '{name}'.", exc_info=True)
                raise SpaceManagerException(
                    f"Failed to delete space '{name}'.",
                    metadata={"space": name},
                    cause=e,
                )

    def list_spaces(self, label_filter: Optional[str] = None) -> List[Space]:
        try:
            spaces_data = self._registry.list_spaces()
            spaces = [Space.from_dict(data) for data in spaces_data]

            return [s for s in spaces if s.label == label_filter] if label_filter else spaces

        except Exception as e:
            logger.error("❌ Failed to list spaces.", exc_info=True)
            raise SpaceManagerException(
                "Failed to list spaces.",
                error_code="LIST_SPACES_FAILED",
                cause=e,
            )

    def rename_space(self, old_name: str, new_name: str) -> Space:
        if not self.space_exists(old_name):
            raise SpaceManagerException(
                f"Space '{old_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": old_name},
            )

        if self.space_exists(new_name):
            raise SpaceManagerException(
                f"A space with the new name '{new_name}' already exists.",
                error_code="SPACE_ALREADY_EXISTS",
                metadata={"space": new_name},
            )

        with SpaceOperationLock(old_name), SpaceOperationLock(new_name):
            try:
                old_space = self.get_space(old_name)
                old_path = old_space.path
                new_path = os.path.join(os.path.dirname(old_path), new_name)

                DirectoryUtils.rename_directory(old_path, new_path)

                new_space = Space(
                    name=new_name,
                    label=old_space.label,
                    parent=old_space.parent,
                    path=new_path,
                    created_at=old_space.created_at,
                    last_modified_at=datetime.datetime.now(datetime.timezone.utc),
                )

                self._registry.remove_space(old_name)
                self._registry.add_space(new_space.name, new_space.to_dict())

                logger.info(f"✏️ Space '{old_name}' successfully renamed to '{new_name}'.")

                return new_space

            except Exception as e:
                logger.error(f"❌ Failed to rename space '{old_name}' to '{new_name}'.", exc_info=True)
                raise SpaceManagerException(
                    f"Failed to rename space '{old_name}' to '{new_name}'.",
                    error_code="RENAME_SPACE_FAILED",
                    metadata={"old_name": old_name, "new_name": new_name},
                    cause=e,
                )
