from typing import Optional
from darca_space_manager.core.interfaces.file_backend import FileBackend
from darca_space_manager.core.backends.local_file_backend import LocalFileBackend


class BackendResolver:
    """
    Central resolver for selecting the active FileBackend implementation.

    In the future, this can load from config/env/registry to support S3, in-memory, etc.
    """

    _default_backend: Optional[FileBackend] = None

    @classmethod
    def get_backend(cls) -> FileBackend:
        if cls._default_backend is None:
            cls._default_backend = LocalFileBackend()
        return cls._default_backend

    @classmethod
    def override_backend(cls, backend: FileBackend):
        """
        Manually override the backend used by default. Useful in tests or advanced deployments.
        """
        cls._default_backend = backend

    @classmethod
    def reset_backend(cls):
        """Clear the override, falling back to default backend."""
        cls._default_backend = None
