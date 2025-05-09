"""
space_operation_lock.py

Provides per-space file-based locking for safe concurrent operations.
"""

import os
import time
import fcntl
from pathlib import Path
from darca_log_facility.logger import DarcaLogger
from darca_space_manager import config

logger = DarcaLogger(name="space_lock").get_logger()


class SpaceOperationLock:
    """
    File-based per-space locking using fcntl.
    Prevents concurrent modification of the same space by using
    a blocking or timed-acquire lock file per space.
    """

    def __init__(self, space_name: str, timeout: int = 30, poll_interval: float = 0.1):
        self.space_name = space_name
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._file_handle = None

        lock_dir = config.get_directories()["METADATA_DIR"]  # ✅ use configured path
        self.lock_file_path = os.path.join(lock_dir, f"{space_name}.lock")

    def __enter__(self):
        os.makedirs(os.path.dirname(self.lock_file_path), exist_ok=True)

        logger.debug(f"🔒 Attempting to acquire lock for space: {self.space_name}")
        self._file_handle = open(self.lock_file_path, "w+")

        start_time = time.time()

        while True:
            try:
                fcntl.flock(self._file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.debug(f"✅ Lock acquired for space: {self.space_name}")
                return self
            except BlockingIOError:
                if (time.time() - start_time) >= self.timeout:
                    logger.error(f"⏱️ Timeout while waiting for lock on space '{self.space_name}'")
                    raise TimeoutError(f"Timeout while acquiring lock for space '{self.space_name}'")
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            fcntl.flock(self._file_handle, fcntl.LOCK_UN)
            logger.debug(f"🔓 Lock released for space: {self.space_name}")
        finally:
            self._file_handle.close()
            # Optional: don't delete lock file to preserve cross-process semantics
