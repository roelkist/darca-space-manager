import os
import time
import fcntl
from typing import Optional

from darca_space_manager import config


class SpaceOperationLock:
    """
    Provides a file-based lock for space operations.

    Ensures that operations on the same space do not overlap
    across threads and processes.
    """

    def __init__(self, space_name: str):
        lock_dir = os.path.join(config.get_directories()["METADATA_DIR"], "locks")
        os.makedirs(lock_dir, exist_ok=True)

        self.lock_file_path = os.path.join(lock_dir, f"{space_name}.lock")
        self.lock_file = None

    def acquire(self, timeout: Optional[int] = None):
        self.lock_file = open(self.lock_file_path, "w")

        start_time = time.time()

        while True:
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return  # Acquired
            except BlockingIOError:
                if timeout is not None and (time.time() - start_time) >= timeout:
                    raise TimeoutError(f"Could not acquire lock for {self.lock_file_path}")

                time.sleep(0.1)  # Wait and retry

    def release(self):
        if self.lock_file:
            fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
            self.lock_file = None

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
