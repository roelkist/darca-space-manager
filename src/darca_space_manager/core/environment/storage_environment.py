from typing import Optional
from darca_space_manager.core.interfaces.storage_connector import StorageConnector
from darca_space_manager.api.space_service import SpaceService
from darca_space_manager.core.interfaces.file_backend import FileBackend


class StorageEnvironment:
    """
    Central environment bootstrapper.

    - Uses a StorageConnector to validate availability and access
    - Instantiates SpaceService with backend wiring
    """

    def __init__(self, connector: StorageConnector):
        self._connector = connector
        self._backend: Optional[FileBackend] = None
        self._service: Optional[SpaceService] = None

    def initialize(self, user: Optional[str] = None) -> SpaceService:
        """
        Validate connection and access, then build a fully wired SpaceService.
        Raises exceptions if initialization fails.
        """
        if not self._connector.verify_connection():
            raise RuntimeError("Storage is not reachable.")

        if not self._connector.verify_access(user=user):
            raise PermissionError("Access to storage is denied.")

        self._backend = self._connector.connect()
        self._service = SpaceService(backend=self._backend)
        return self._service

    def get_backend(self) -> FileBackend:
        if not self._backend:
            raise RuntimeError("Environment not initialized.")
        return self._backend

    def get_service(self) -> SpaceService:
        if not self._service:
            raise RuntimeError("Environment not initialized.")
        return self._service
