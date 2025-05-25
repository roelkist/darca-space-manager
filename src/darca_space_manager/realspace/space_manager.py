"""
api/space_manager.py

High-level API for managing logical spaces with access control.
"""
#FIXME: moving to core, instance create by parsing all, managed above

import datetime
import os
from typing import Dict, List, Optional
from contextlib import contextmanager

from darca_exception.exception import DarcaException
from darca_log_facility.logger import DarcaLogger
from darca_storage.interfaces.file_backend import FileBackend

from darca_space_manager.metaspace.models import Space

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
    API layer for managing logical spaces with ownership and access control.
    """

    def __init__(
            self, 
            backend: FileBackend,
            ):
        self._backend = backend

    def _assert_access(self, space: Space, user: Optional[str]):
        if user is None:
            return
        if space.owner == user:
            return
        if space.permissions and user in space.permissions:
            return
        raise SpaceManagerException(
            f"Access denied for user '{user}' on space '{space.name}'.",
            error_code="ACCESS_DENIED",
            metadata={"space": space.name, "user": user}
        )

    def space_exists(self, name: str) -> bool:
        return True

    def get_space(self, name: str) -> Optional[Space]:
        return True

    def get_space_info(self, name: str, user: Optional[str] = None) -> Space:
        return True 

    def _compute_space_last_modified(self, path: str) -> float:
        entries = self._backend.list(path, recursive=True)
        latest = 0.0
        for entry in entries:
            full_path = os.path.join(path, entry)
            try:
                if self._backend.exists(full_path):
                    mtime = self._backend.stat_mtime(full_path)
                    latest = max(latest, mtime)
            except Exception:
                pass
        return latest or self._backend.stat_mtime(path)

    def create_space(
        self,
        name: str,
        user: Optional[str] = None,
    ) -> bool:
        if self.space_exists(name):
            raise SpaceManagerException(
                f"Space '{name}' already exists.",
                metadata={"space": name},
            )

        try:
            self._backend.mkdir(name, user=user)
            logger.info(f"✅ Realspace '{name}' created.")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create space '{name}'.", exc_info=True)
            raise SpaceManagerException(
                f"Failed to create space '{name}'.",
                error_code="CREATE_SPACE_FAILED",
                metadata={"space": name},
                cause=e,
            )

    def delete_space(self, name: str, force: bool = False, user: Optional[str] = None) -> bool:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        self._assert_access(space, user)
        
        try:
            self._backend.rmdir(name)

        except Exception as e:
            logger.error(f"❌ Failed to delete space '{name}'", exc_info=True)
            raise SpaceManagerException(
                message=f"Failed to delete space '{name}'.",
                error_code="DELETE_SPACE_FAILED",
                metadata={"space": name, "force": force},
                cause=e,
            )

    def list_spaces(self, label_filter: Optional[str] = None, user: Optional[str] = None) -> List[Space]:
        return []

    def rename_space(self, old_name: str, new_name: str, user: Optional[str] = None) -> Space:
        old_space = self.get_space(old_name)
        if not old_space:
            raise SpaceManagerException(
                f"Space '{old_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": old_name},
            )
        try:
            self._backend.rename(old_name, new_name)
            logger.info(f"✏️ Space '{old_name}' successfully renamed to '{new_name}'")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to rename space '{old_name}' to '{new_name}'", exc_info=True)
            raise SpaceManagerException(
                f"Failed to rename space '{old_name}' to '{new_name}'.",
                error_code="RENAME_SPACE_FAILED",
                metadata={"old_name": old_name, "new_name": new_name},
                cause=e,
            )
