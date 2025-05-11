from typing import List, Union, Protocol


class FileBackend(Protocol):
    """
    Protocol for backend-agnostic file and directory operations.

    Implementations may target local filesystems, remote storage (e.g., S3), 
    or virtual in-memory stores. All paths are treated as opaque strings.
    """

    def read(self, path: str, binary: bool = False) -> Union[str, bytes]:
        """Read the contents of a file."""
        ...

    def write(self, path: str, content: Union[str, bytes]):
        """Write contents to a file. Overwrites if it exists."""
        ...

    def delete(self, path: str):
        """Remove a file."""
        ...

    def exists(self, path: str) -> bool:
        """Check whether the given file or directory exists."""
        ...

    def list(self, base_path: str, recursive: bool = False) -> List[str]:
        """List contents of a directory."""
        ...

    def mkdir(self, path: str, parents: bool = True):
        """Create a directory."""
        ...

    def rmdir(self, path: str):
        """Remove a directory recursively."""
        ...

    def rename(self, src: str, dest: str):
        """Rename or move a file/directory."""
        ...

    def stat_mtime(self, path: str) -> float:
        """Return the last modification time (epoch) of a file or directory."""
        ...
