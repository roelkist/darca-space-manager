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

from darca_space_manager.realspace.space_path_service import SpacePathService

from darca_space_manager.metaspace.models import Space
from darca_space_manager.metaspace.metaspace_backend import MetaspaceBackend

from darca_space_manager.lock.lock_manager import LockManager
from darca_space_manager.lock.operation_lock import OperationLock

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
            metadata_repo: MetaspaceBackend,
            lock_manager: LockManager,
            path_service: SpacePathService,
            ):
        self._backend = backend
        self._registry = metadata_repo
        self._locks = lock_manager
        self._path = path_service
        
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
        return self._registry.get_space(name) is not None

    def get_space(self, name: str) -> Optional[Space]:
        data = self._registry.get_space(name)
        return Space.from_dict(data) if data else None

    def get_space_info(self, name: str, user: Optional[str] = None) -> Space:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        self._assert_access(space, user)

        latest_timestamp = self._compute_space_last_modified(space.path)
        space.last_modified_at = datetime.datetime.fromtimestamp(latest_timestamp, datetime.timezone.utc)
        return space

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
        label: str = "",
        parent_path: Optional[str] = None,
        user: Optional[str] = None,
    ) -> Space:
        if self.space_exists(name):
            raise SpaceManagerException(
                f"Space '{name}' already exists.",
                metadata={"space": name},
            )

        with OperationLock(name):
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

                    self._assert_access(base_space, user)

                    base_path = base_space.path
                    destination_path = os.path.normpath(os.path.join(base_path, relative_subpath, name))

                    SpacePathService().ensure_within_space(base_path, destination_path)
                    self._backend.mkdir(os.path.dirname(destination_path), parents=True)
                else:
                    destination_path = os.path.join(
                        self._registry.load_registry().get("base_path", os.path.expanduser("~/.local/share/darca_space/spaces")),
                        name,
                    )

                self._backend.mkdir(destination_path)

                space = Space(
                    name=name,
                    label=label,
                    parent=parent_path,
                    path=destination_path,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    last_modified_at=datetime.datetime.now(datetime.timezone.utc),
                    owner=user,
                    permissions=[user] if user else None,
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

    def delete_space(self, name: str, force: bool = False, user: Optional[str] = None) -> bool:
        space = self.get_space(name)
        if not space:
            raise SpaceManagerException(
                f"Space '{name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": name},
            )

        self._assert_access(space, user)
        base_path = space.path

        nested = [
            s for s in self._registry.list_spaces()
            if s["name"] != name and s["path"].startswith(base_path + os.sep)
        ]

        if nested and not force:
            raise SpaceManagerException(
                message=f"Cannot delete space '{name}' — it contains subspaces.",
                error_code="SUBSPACES_EXIST",
                metadata={"space": name, "subspaces": [s["name"] for s in nested]},
            )

        lock_names = [name] + [s["name"] for s in nested]
        try:
            with self._acquire_multiple_locks(lock_names):
                self._backend.rmdir(base_path)

                self._registry.remove_space(name)
                for sub in nested:
                    self._registry.remove_space(sub["name"])

                logger.info(f"🗑️ Space '{name}' deleted (force={force}).")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to delete space '{name}'", exc_info=True)
            raise SpaceManagerException(
                message=f"Failed to delete space '{name}'.",
                error_code="DELETE_SPACE_FAILED",
                metadata={"space": name, "force": force},
                cause=e,
            )

    def list_spaces(self, label_filter: Optional[str] = None, user: Optional[str] = None) -> List[Space]:
        try:
            spaces_data = self._registry.list_spaces()
            spaces = [Space.from_dict(data) for data in spaces_data]

            if label_filter:
                spaces = [s for s in spaces if s.label == label_filter]

            if user:
                spaces = [s for s in spaces if s.owner == user or (s.permissions and user in s.permissions)]

            return spaces

        except Exception as e:
            logger.error("❌ Failed to list spaces.", exc_info=True)
            raise SpaceManagerException(
                "Failed to list spaces.",
                error_code="LIST_SPACES_FAILED",
                cause=e,
            )

    def rename_space(self, old_name: str, new_name: str, user: Optional[str] = None) -> Space:
        old_space = self.get_space(old_name)
        if not old_space:
            raise SpaceManagerException(
                f"Space '{old_name}' does not exist.",
                error_code="SPACE_NOT_FOUND",
                metadata={"space": old_name},
            )

        self._assert_access(old_space, user)

        if self.space_exists(new_name):
            raise SpaceManagerException(
                f"A space with the new name '{new_name}' already exists.",
                error_code="SPACE_ALREADY_EXISTS",
                metadata={"space": new_name},
            )

        old_path = old_space.path
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        for s in self._registry.list_spaces():
            if s["name"] in (old_name, new_name):
                continue
            if s["path"] == new_path or s["path"].startswith(new_path + os.sep):
                raise SpaceManagerException(
                    message=f"Cannot rename '{old_name}' → '{new_name}': target path conflicts with space '{s['name']}'",
                    error_code="RENAME_COLLISION",
                    metadata={"conflict": s["name"], "target_path": new_path},
                )

        with OperationLock(old_name), OperationLock(new_name):
            try:
                self._backend.rename(old_path, new_path)

                updated = Space(
                    name=new_name,
                    path=new_path,
                    label=old_space.label,
                    parent=old_space.parent,
                    created_at=old_space.created_at,
                    last_modified_at=datetime.datetime.now(datetime.timezone.utc),
                    owner=old_space.owner,
                    permissions=old_space.permissions,
                )

                self._registry.remove_space(old_name)
                self._registry.add_space(new_name, updated.to_dict())

                logger.info(f"✏️ Space '{old_name}' successfully renamed to '{new_name}'")
                return updated

            except Exception as e:
                logger.error(f"❌ Failed to rename space '{old_name}' to '{new_name}'", exc_info=True)
                raise SpaceManagerException(
                    f"Failed to rename space '{old_name}' to '{new_name}'.",
                    error_code="RENAME_SPACE_FAILED",
                    metadata={"old_name": old_name, "new_name": new_name},
                    cause=e,
                )

    @contextmanager
    def _acquire_multiple_locks(self, space_names: list):
        locks = [OperationLock(n) for n in sorted(set(space_names))]
        try:
            for lock in locks:
                lock.__enter__()
            yield
        finally:
            for lock in reversed(locks):
                lock.__exit__(None, None, None)
