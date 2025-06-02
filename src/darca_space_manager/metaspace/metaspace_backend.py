# License: MIT

from abc import ABC, abstractmethod
from typing import List, Dict


class MetaspaceBackend(ABC):
    """
    Abstract interface for managing space metadata.

    Provides explicit, field-level setters and encapsulates all timestamp handling.
    """

    # ------------------------
    # Core Operations
    # ------------------------

    @abstractmethod
    def get_space(self, name: str) -> dict:
        """Fetch metadata dict for a given space name."""
        ...

    @abstractmethod
    def list_spaces(self) -> List[dict]:
        """List all space metadata entries."""
        ...

    @abstractmethod
    def add_space(
        self,
        name: str,
        label: str = "",
        repository: str = "",
        owner: str = "default_user",
        permissions: List[str] = None,
    ):
        """
        Create or update a space metadata entry.
        Automatically sets created_at (only if new) and updates last_modified_at.
        """
        ...

    @abstractmethod
    def remove_space(self, name: str):
        """Delete a space's metadata."""
        ...

    @abstractmethod
    def rename_space(self, old_name: str, new_name: str) -> dict:
        """
        Rename a space and update its internal name attribute.
        Automatically updates last_modified_at.
        """
        ...

    # ------------------------
    # Attribute Setters
    # ------------------------

    @abstractmethod
    def set_label(self, name: str, label: str) -> dict:
        ...

    @abstractmethod
    def set_repository(self, name: str, repository: str) -> dict:
        ...

    @abstractmethod
    def set_owner(self, name: str, owner: str) -> dict:
        ...

    @abstractmethod
    def set_permissions(self, name: str, permissions: List[str]) -> dict:
        ...

    # ------------------------
    # Timestamp Controls (internal use)
    # ------------------------

    @abstractmethod
    def set_created_at(self, name: str, timestamp: str) -> dict:
        """Manually override creation time (rare)."""
        ...

    @abstractmethod
    def set_last_modified_at(self, name: str, timestamp: str) -> dict:
        """Manually override last modified time."""
        ...

    @abstractmethod
    def touch(self, name: str) -> dict:
        """Update last_modified_at to current time."""
        ...

    # ------------------------
    # Registry Snapshot
    # ------------------------

    @abstractmethod
    def load_registry(self) -> Dict:
        """Return raw registry snapshot for diagnostics."""
        ...
