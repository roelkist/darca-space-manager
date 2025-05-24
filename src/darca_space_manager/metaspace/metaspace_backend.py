# space_metadata_repository.py
# License: MIT

from abc import ABC, abstractmethod
from typing import List, Dict


class MetaspaceBackend(ABC):
    """
    Abstract interface for storing and retrieving space metadata.

    Allows pluggable implementations such as:
        - YAML files
        - SQL databases
        - Key-value stores
        - Remote APIs
    """

    @abstractmethod
    def get_space(self, name: str) -> dict:
        """Fetch metadata dict for a given space name."""
        ...

    @abstractmethod
    def list_spaces(self) -> List[dict]:
        """List all space metadata entries."""
        ...

    @abstractmethod
    def add_space(self, name: str, space_dict: dict):
        """Insert or update a space's metadata."""
        ...

    @abstractmethod
    def remove_space(self, name: str):
        """Remove a space from metadata."""
        ...

    @abstractmethod
    def load_registry(self) -> Dict:
        """Return raw registry data (for low-level read-only access)."""
        ...
