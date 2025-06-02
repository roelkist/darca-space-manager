# file_lock_manager.py
# License: MIT

from typing import List
from contextlib import AbstractContextManager, ExitStack, asynccontextmanager
from darca_space_manager.lock.lock_manager import LockManager
from darca_space_manager.lock.operation_lock import OperationLock

class FileLockManager(LockManager):
    """
    Lock manager using per-space file-based locks (via fcntl).
    Wraps SpaceOperationLock for interface compatibility.
    """

    def acquire(self, space_name: str):
        @asynccontextmanager
        async def async_lock():
            with OperationLock(space_name):
                yield
        return async_lock()

    def acquire_many(self, space_names: List[str]):
        @asynccontextmanager
        async def async_multi_lock():
            with ExitStack() as stack:
                for name in sorted(set(space_names)):
                    stack.enter_context(OperationLock(name))
                yield
        return async_multi_lock()
