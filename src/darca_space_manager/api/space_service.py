# src/darca_space_manager/api/space_service.py
# License: MIT

from typing import Optional, Union, List, Dict
from datetime import datetime

from darca_storage.client import StorageClient
from darca_space_manager.lock.lock_manager import LockManager
from darca_space_manager.metaspace.models import Space, SpaceURI
from darca_space_manager.iospace.iospace_file import IOSpaceFile
from darca_space_manager.iospace.iospace_exec import IOSpaceExec
from darca_space_manager.metaspace.metaspace_backend import MetaspaceBackend
from darca_space_manager.masterspace.masterspace_backend import MasterspaceBackend


class SpaceService:
    def __init__(
        self,
        metaspace: MetaspaceBackend,
        lock_manager: LockManager,
        masterspace_backend: MasterspaceBackend,
    ):
        self._metaspace = metaspace
        self._lock_manager = lock_manager
        self._masterspace_backend = masterspace_backend

    # ------------------------
    # Metadata
    # ------------------------

    async def get_space(self, name: str) -> Optional[Space]:
        data = self._metaspace.get_space(name)
        return Space.from_dict(data) if data else None

    async def list_spaces(self, label: Optional[str] = None, user: Optional[str] = None) -> List[Space]:
        return [
            Space.from_dict(s)
            for s in self._metaspace.list_spaces()
            if not label or s.get("label") == label
        ]

    async def create_space(
        self,
        name: str,
        repository: str,
        *,
        label: Optional[str] = None,
        owner: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        user: Optional[str] = None,
    ) -> Space:
        async with self._lock_manager.acquire(name):
            self._metaspace.add_space(
                name=name,
                label=label or "",
                repository=repository,
                owner=owner or user or "default_user",
                permissions=permissions or ["read", "write"],
            )

            space = await self.get_space(name)
            client = await self._masterspace_backend.get_client(name)
            iospace = IOSpaceFile(space=space, client=client)
            await iospace.create_dir(name)

            return space

    async def delete_space(self, name: str, force: bool = False, user: Optional[str] = None) -> bool:
        space = await self.get_space(name)
        if not space:
            return False

        base_prefix = name + "/"
        nested = [
            Space.from_dict(s)
            for s in self._metaspace.list_spaces()
            if s["name"] != name and s["name"].startswith(base_prefix)
        ]
        lock_names = [name] + [s.name for s in nested]

        async with self._lock_manager.acquire_many(lock_names):
            client = await self._masterspace_backend.get_client(name)
            iospace = IOSpaceFile(space=space, client=client)
            await iospace.delete_dir(name)

            self._metaspace.remove_space(name)
            for s in nested:
                self._metaspace.remove_space(s.name)

            return True

    async def rename_space(self, old_name: str, new_name: str, user: Optional[str] = None) -> Space:
        async with self._lock_manager.acquire_many([old_name, new_name]):
            old_space = await self.get_space(old_name)
            if not old_space:
                raise ValueError(f"Space '{old_name}' does not exist")

            client = await self._masterspace_backend.get_client(old_name)
            iospace = IOSpaceFile(space=old_space, client=client)
            await iospace.move(old_name, new_name)

            self._metaspace.rename_space(old_name, new_name)

            return await self.get_space(new_name)

    async def set_label(self, name: str, label: str) -> Space:
        async with self._lock_manager.acquire(name):
            self._metaspace.set_label(name, label)
            return await self.get_space(name)

    # ------------------------
    # File I/O
    # ------------------------

    async def read_file(self, uri: Union[str, SpaceURI], *, load: bool = False, user: Optional[str] = None):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        space = await self.get_space(uri.space_name)
        client = await self._masterspace_backend.get_client(uri.space_name)
        return await IOSpaceFile(space=space, client=client).read_file(uri.path, load=load)

    async def write_file(self, uri: Union[str, SpaceURI], content: Union[str, dict], *, user: Optional[str] = None):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        async with self._lock_manager.acquire(uri.space_name):
            space = await self.get_space(uri.space_name)
            client = await self._masterspace_backend.get_client(uri.space_name)
            await IOSpaceFile(space=space, client=client).write_file(uri.path, content)
            self._metaspace.touch(uri.space_name)
            return True

    async def delete_file(self, uri: Union[str, SpaceURI], *, user: Optional[str] = None):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        async with self._lock_manager.acquire(uri.space_name):
            space = await self.get_space(uri.space_name)
            client = await self._masterspace_backend.get_client(uri.space_name)
            await IOSpaceFile(space=space, client=client).delete_file(uri.path)
            self._metaspace.touch(uri.space_name)
            return True

    async def file_exists(self, uri: Union[str, SpaceURI], *, user: Optional[str] = None) -> bool:
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        space = await self.get_space(uri.space_name)
        client = await self._masterspace_backend.get_client(uri.space_name)
        return await IOSpaceFile(space=space, client=client).file_exists(uri.path)

    async def file_last_modified(self, uri: Union[str, SpaceURI], *, user: Optional[str] = None) -> float:
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        space = await self.get_space(uri.space_name)
        client = await self._masterspace_backend.get_client(uri.space_name)
        return await IOSpaceFile(space=space, client=client).file_last_modified(uri.path)

    # ------------------------
    # Directory Operations
    # ------------------------

    async def create_dir(self, uri: Union[str, SpaceURI], user: Optional[str] = None):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        async with self._lock_manager.acquire(uri.space_name):
            space = await self.get_space(uri.space_name)
            client = await self._masterspace_backend.get_client(uri.space_name)
            await IOSpaceFile(space=space, client=client).create_dir(uri.path)
            self._metaspace.touch(uri.space_name)

    async def delete_dir(self, uri: Union[str, SpaceURI], user: Optional[str] = None):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        async with self._lock_manager.acquire(uri.space_name):
            space = await self.get_space(uri.space_name)
            client = await self._masterspace_backend.get_client(uri.space_name)
            await IOSpaceFile(space=space, client=client).delete_dir(uri.path)
            self._metaspace.touch(uri.space_name)

    async def move_path(self, uri_from: Union[str, SpaceURI], uri_to: Union[str, SpaceURI], user: Optional[str] = None):
        uri_from = SpaceURI.from_str(uri_from) if isinstance(uri_from, str) else uri_from
        uri_to = SpaceURI.from_str(uri_to) if isinstance(uri_to, str) else uri_to

        if uri_from.space_name != uri_to.space_name:
            raise ValueError("Cannot move paths between different spaces.")

        async with self._lock_manager.acquire(uri_from.space_name):
            space = await self.get_space(uri_from.space_name)
            client = await self._masterspace_backend.get_client(uri_from.space_name)
            await IOSpaceFile(space=space, client=client).move(uri_from.path, uri_to.path)
            self._metaspace.touch(uri_from.space_name)

    # ------------------------
    # Execution
    # ------------------------

    async def run(
        self,
        uri: Union[str, SpaceURI],
        command: Union[List[str], str],
        *,
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
        user: Optional[str] = None,
    ):
        uri = SpaceURI.from_str(uri) if isinstance(uri, str) else uri
        async with self._lock_manager.acquire(uri.space_name):
            space = await self.get_space(uri.space_name)
            client = await self._masterspace_backend.get_client(uri.space_name)
            executor = IOSpaceExec(space=space, client=client)
            result = await executor.run(
                command=command,
                capture_output=capture_output,
                check=check,
                env=env,
                timeout=timeout,
                user=user,
            )
            self._metaspace.touch(uri.space_name)
            return result
