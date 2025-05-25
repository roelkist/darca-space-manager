from typing import Optional, Union, List, Dict
from darca_storage.interfaces.file_backend import FileBackend

from darca_space_manager.lock.lock_manager import LockManager
from darca_space_manager.metaspace.metaspace_backend import MetaspaceBackend
from darca_space_manager.metaspace.models import Space, SpaceURI

from darca_space_manager.realspace.space_manager import SpaceManager
from darca_space_manager.realspace.space_file_manager import SpaceFileManager
from darca_space_manager.realspace.space_executor import SpaceExecutor
from darca_space_manager.realspace.space_path_service import SpacePathService


class SpaceService:
    def __init__(
        self,
        backend: FileBackend,
        metaspace: MetaspaceBackend,
        lock_manager: LockManager,
    ):
        self._backend = backend
        self._metaspace = metaspace
        self._lock_manager = lock_manager
        self._path_service = SpacePathService()

        self._manager = SpaceManager(
            backend=self._backend,
            metadata_repo=self._metaspace,
            lock_manager=self._lock_manager,  # no-op inside manager
            path_service=self._path_service,
        )
        self._file_manager = SpaceFileManager(space_manager=self._manager)
        self._executor = SpaceExecutor(space_manager=self._manager)

    # --- Space Lifecycle ---

    def create_space(self, name: str, label: str = "", parent: Optional[str] = None, user: Optional[str] = None) -> Space:
        with self._lock_manager.acquire(name):
            space = self._manager.create_space(name, label=label, parent_path=parent, user=user)
            self._metaspace.add_space(space.name, space.to_dict())
            return space

    def delete_space(self, name: str, force: bool = False, user: Optional[str] = None) -> bool:
        space_data = self._metaspace.get_space(name)
        if not space_data:
            return False

        base_path = space_data["path"]
        nested = [
            s for s in self._metaspace.list_spaces()
            if s["name"] != name and s["path"].startswith(base_path + "/")
        ]

        if nested and not force:
            raise ValueError(f"Space '{name}' contains subspaces: {[s['name'] for s in nested]}")

        lock_names = [name] + [s["name"] for s in nested]
        with self._lock_manager.acquire_many(lock_names):
            result = self._manager.delete_space(name, force=force, user=user)
            self._metaspace.remove_space(name)
            for sub in nested:
                self._metaspace.remove_space(sub["name"])
            return result

    def rename_space(self, old_name: str, new_name: str, user: Optional[str] = None) -> Space:
        with self._lock_manager.acquire_many([old_name, new_name]):
            updated = self._manager.rename_space(old_name, new_name, user=user)
            self._metaspace.remove_space(old_name)
            self._metaspace.add_space(new_name, updated.to_dict())
            return updated

    def get_space(self, name: str) -> Optional[Space]:
        data = self._metaspace.get_space(name)
        return Space.from_dict(data) if data else None

    def get_space_info(self, name: str, user: Optional[str] = None) -> Space:
        return self._manager.get_space_info(name, user=user)

    def list_spaces(self, label_filter: Optional[str] = None, user: Optional[str] = None) -> List[Space]:
        return self._manager.list_spaces(label_filter=label_filter, user=user)

    # --- File Operations ---

    def file_exists(self, uri: Union[str, SpaceURI], user: Optional[str] = None) -> bool:
        return self._file_manager.file_exists(uri, user=user)

    def read_file(self, uri: Union[str, SpaceURI], load: bool = False, user: Optional[str] = None) -> Union[str, dict]:
        return self._file_manager.get_file(uri, load=load, user=user)

    def write_file(self, uri: Union[str, SpaceURI], content: Union[str, dict], user: Optional[str] = None) -> bool:
        with self._lock_manager.acquire(uri.space_name):
            return self._file_manager.set_file(uri, content, user=user)

    def delete_file(self, uri: Union[str, SpaceURI], user: Optional[str] = None) -> bool:
        with self._lock_manager.acquire(uri.space_name):
            return self._file_manager.delete_file(uri, user=user)

    def list_files(self, space_name: str, recursive: bool = False, files_only: bool = False, user: Optional[str] = None) -> List[str]:
        return self._file_manager.list_files(space_name, recursive=recursive, files_only=files_only, user=user)

    def list_files_content(self, space_name: str, user: Optional[str] = None) -> List[dict]:
        return self._file_manager.list_files_content(space_name, user=user)

    def file_last_modified(self, uri: Union[str, SpaceURI], user: Optional[str] = None) -> float:
        return self._file_manager.get_file_last_modified(uri, user=user)

    # --- Command Execution ---

    def run(
        self,
        uri: Union[str, SpaceURI],
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
        user: Optional[str] = None,
    ):
        with self._lock_manager.acquire(uri.space_name):
            return self._executor.run_in_space(
                uri=uri,
                command=command,
                capture_output=capture_output,
                check=check,
                env=env,
                timeout=timeout,
                user=user,
            )
