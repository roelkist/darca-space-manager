from abc import ABC, abstractmethod
from typing import Optional
from darca_space_manager.core.interfaces.file_backend import FileBackend


class StorageConnector(ABC):
    """
    Abstract interface for connecting to a storage backend.

    Implementations must:
    - Connect and return a FileBackend.
    - Verify the backend is available.
    - Verify that access is permitted.
    """

    @abstractmethod
    def connect(self) -> FileBackend:
        """Return a FileBackend instance if connection succeeds."""
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """Return True if the backend is reachable."""
        pass

    @abstractmethod
    def verify_access(self, user: Optional[str] = None) -> bool:
        """
        Return True if the user is permitted to access the root/base of the storage.
        If user is None, check default environment context.
        """
        pass
