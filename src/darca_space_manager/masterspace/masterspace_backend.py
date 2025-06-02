# masterspace/masterspace_backend.py

from abc import ABC, abstractmethod
from darca_space_manager.metaspace.models import Space
from darca_storage.client import StorageClient

class MasterspaceBackend(ABC):
    @abstractmethod
    async def get_client(self, space: Space) -> StorageClient:
        ...
