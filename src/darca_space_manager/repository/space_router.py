# space_router.py
# License: MIT

import asyncio
from typing import Dict
from darca_space_manager.metaspace.models import SpaceURI
from darca_space_manager.repository.repository_backend import RepositoryBackend
from darca_storage.factory import StorageConnectorFactory
from darca_storage.interfaces.file_backend import FileBackend


class SpaceRouter:
    """
    Resolves a space://<space>/<path> URI into a concrete FileBackend.
    Profiles are managed via a SpaceBackendRepository.
    Connectors are cached per space for efficiency.
    """

    def __init__(self, repository: RepositoryBackend):
        self._repository = repository
        self._connector_cache: Dict[str, FileBackend] = {}

    async def resolve_backend(self, uri: str | SpaceURI) -> FileBackend:
        if isinstance(uri, str):
            uri = SpaceURI.from_str(uri)

        space_name = uri.space_name

        # Return cached backend if already resolved
        if space_name in self._connector_cache:
            return self._connector_cache[space_name]

        profile = self._repository.get_profile(space_name)
        connector = await StorageConnectorFactory.from_url(
            profile.storage_url,
            # Optional: pass credentials or parameters here if your factory supports it
        )
        backend = await connector.connect()
        self._connector_cache[space_name] = backend
        return backend
