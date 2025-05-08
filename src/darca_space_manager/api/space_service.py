"""
api/space_service.py

Unified API service for managing spaces, files, metadata and command execution.
"""

from typing import Optional, Union, List, Dict
from darca_space_manager.api.space_manager import SpaceManager
from darca_space_manager.api.space_file_manager import SpaceFileManager
from darca_space_manager.api.space_executor import SpaceExecutor
from darca_space_manager.models.space_uri import SpaceURI
from darca_space_manager.models.space import Space


class SpaceService:
    """
    Unified API layer for managing logical spaces, files, and command execution.
    """

    def __init__(self):
        self._manager = SpaceManager()
        self._file_manager = SpaceFileManager()
        self._executor = SpaceExecutor()

    # -- Space Lifecycle --

    def create_space(self, name: str, label: str = "", parent: Optional[str] = None) -> Space:
        return self._manager.create_space(name, label, parent)

    def delete_space(self, name: str) -> bool:
        return self._manager.delete_space(name)

    def rename_space(self, old_name: str, new_name: str) -> Space:
        return self._manager.rename_space(old_name, new_name)

    def get_space(self, name: str) -> Optional[Space]:
        return self._manager.get_space(name)

    def get_space_info(self, name: str) -> Space:
        return self._manager.get_space_info(name)

    def list_spaces(self, label_filter: Optional[str] = None) -> List[Space]:
        return self._manager.list_spaces(label_filter)

    # -- File operations --

    def file_exists(self, uri: Union[str, SpaceURI]) -> bool:
        return self._file_manager.file_exists(uri)

    def read_file(self, uri: Union[str, SpaceURI], load: bool = False) -> Union[str, dict]:
        return self._file_manager.get_file(uri, load=load)

    def write_file(self, uri: Union[str, SpaceURI], content: Union[str, dict]) -> bool:
        return self._file_manager.set_file(uri, content)

    def delete_file(self, uri: Union[str, SpaceURI]) -> bool:
        return self._file_manager.delete_file(uri)

    def list_files(self, space_name: str, recursive: bool = False, files_only: bool = False) -> List[str]:
        return self._file_manager.list_files(space_name, recursive, files_only)

    def list_files_content(self, space_name: str) -> List[dict]:
        return self._file_manager.list_files_content(space_name)

    def file_last_modified(self, uri: Union[str, SpaceURI]) -> float:
        return self._file_manager.get_file_last_modified(uri)

    # -- Command execution --

    def run(
        self,
        uri: Union[str, SpaceURI],
        command: Union[List[str], str],
        capture_output: bool = True,
        check: bool = True,
        env: Optional[dict] = None,
        timeout: Optional[int] = 30,
    ):
        return self._executor.run_in_space(
            uri=uri,
            command=command,
            capture_output=capture_output,
            check=check,
            env=env,
            timeout=timeout,
        )
