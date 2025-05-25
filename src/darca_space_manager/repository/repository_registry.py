# space_backend_repository.py
# License: MIT

from abc import ABC, abstractmethod
from typing import List
from darca_space_manager.repository.models import Repository


class RepositoryRegistry(ABC):
    """
    Abstract interface for loading and managing space backend profiles.

    Implementations may load profiles from:
        • Local YAML files
        • Databases (PostgreSQL, SQLite, etc.)
        • Remote APIs or config services
    """

    @abstractmethod
    def get_profile(self, name: str) -> Repository:
        """
        Retrieve a single backend profile by its name.

        Raises:
            KeyError if the profile does not exist.
        """
        ...

    @abstractmethod
    def list_profiles(self) -> List[Repository]:
        """
        Return a list of all available backend profiles.
        """
        ...
