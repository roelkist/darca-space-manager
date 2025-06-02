# masterspace/masterspace_repository_backend.py

from darca_repository import get_repository_registry, RepositoryInstance
from darca_repository.exceptions import RepositoryConnectionError
from darca_space_manager.masterspace.masterspace_backend import MasterspaceBackend
from darca_storage.client import StorageClient

class RepositoryMasterspaceBackend(MasterspaceBackend):
    def __init__(self):
        self._client_cache: dict[str, StorageClient] = {}

    async def get_client(self, repo: str) -> StorageClient:
        if repo in self._client_cache:
            return self._client_cache[repo]

        profile = get_repository_registry().get_profile(repo)
        try:
            client = await RepositoryInstance(profile).connect()
            self._client_cache[repo] = client
            return client
        except RepositoryConnectionError as e:
            raise RuntimeError(f"Could not connect to repository: {repo}") from e
