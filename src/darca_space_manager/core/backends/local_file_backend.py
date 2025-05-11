import os
from typing import List, Union
from darca_file_utils.file_utils import FileUtils
from darca_file_utils.directory_utils import DirectoryUtils
from darca_space_manager.core.interfaces.file_backend import FileBackend


class LocalFileBackend(FileBackend):
    """
    Local disk-based implementation of the FileBackend protocol.
    Delegates to darca-file-utils.
    """

    def read(self, path: str, binary: bool = False) -> Union[str, bytes]:
        mode = "rb" if binary else "r"
        return FileUtils.read_file(path, mode=mode, encoding=None if binary else "utf-8")

    def write(self, path: str, content: Union[str, bytes]):
        if isinstance(content, str):
            FileUtils.write_file(path, content)
        elif isinstance(content, bytes):
            with open(path, "wb") as f:
                f.write(content)
        else:
            raise TypeError(f"Unsupported content type: {type(content)}")

    def delete(self, path: str):
        FileUtils.remove_file(path)

    def exists(self, path: str) -> bool:
        if DirectoryUtils.directory_exist(path):
            return True
        
        if FileUtils.file_exist(path):
            return True
        
        return False

    def list(self, base_path: str, recursive: bool = False) -> List[str]:
        return DirectoryUtils.list_directory(base_path, recursive=recursive)

    def mkdir(self, path: str, parents: bool = True):
        DirectoryUtils.create_directory(path)

    def rmdir(self, path: str):
        DirectoryUtils.remove_directory(path)

    def rename(self, src: str, dest: str):
        DirectoryUtils.rename_directory(src, dest)

    def stat_mtime(self, path: str) -> float:
        return os.path.getmtime(path)
