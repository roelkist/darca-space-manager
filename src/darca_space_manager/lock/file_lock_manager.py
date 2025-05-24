# file_lock_manager.py
# License: MIT

from typing import List
from contextlib import AbstractContextManager, ExitStack
from darca_space_manager.lock.lock_manager import LockManager
from darca_space_manager.lock.operation_lock import OperationLock


class FileLockManager(LockManager):
    """
    Lock manager using per-space file-based locks (via fcntl).
    Wraps SpaceOperationLock for interface compatibility.
    """

    def acquire(self, space_name: str) -> AbstractContextManager:
        return OperationLock(space_name)

    def acquire_many(self, space_names: List[str]) -> AbstractContextManager:
        class MultiLockContext(AbstractContextManager):
            def __init__(self, names: List[str]):
                self._names = sorted(set(names))
                self._stack = ExitStack()

            def __enter__(self):
                for name in self._names:
                    self._stack.enter_context(OperationLock(name))
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self._stack.__exit__(exc_type, exc_val, exc_tb)

        return MultiLockContext(space_names)
