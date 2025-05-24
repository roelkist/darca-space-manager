# space_lock_manager.py
# License: MIT

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import List


class LockManager(ABC):
    """
    Abstract interface for acquiring exclusive locks on space operations.

    Supports single and multi-space locking. Useful for local file locks, Redis,
    database row locks, etc.
    """

    @abstractmethod
    def acquire(self, space_name: str) -> AbstractContextManager:
        """
        Acquire a lock for a single space.

        Returns:
            A context manager for `with` usage.
        """
        ...

    @abstractmethod
    def acquire_many(self, space_names: List[str]) -> AbstractContextManager:
        """
        Acquire multiple space locks at once (sorted internally to avoid deadlocks).
        """
        ...
