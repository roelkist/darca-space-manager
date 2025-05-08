import os
from typing import Union, List
from datetime import datetime, timezone

from darca_yaml.yaml_utils import YamlUtils
from darca_log_facility.logger import DarcaLogger
from darca_space_manager.space_file_manager import SpaceFileManager
from darca_space_manager.space_manager import SpaceManager, SpaceManagerException
from darca_space_manager import config

log = DarcaLogger(name="project_space").get_logger()

class Space:
    def __init__(self, space_name: str):
        self.space_name = space_name
        self._space_manager = SpaceManager()
        self._file_manager = SpaceFileManager()
        self._control_dir = config.get_directories()["CONTROL_DIR"]
        self._control_file = os.path.join(self._control_dir, f"{space_name}.yaml")

        if not self._space_manager.space_exists(space_name):
            raise SpaceManagerException(f"Project space '{space_name}' does not exist.")

    def _load_state(self) -> dict:
        if not os.path.exists(self._control_file):
            return {}
        return YamlUtils.load_yaml_file(self._control_file) or {}

    def _save_state(self, state: dict) -> bool:
        return YamlUtils.save_yaml_file(self._control_file, state)

    def _current_utc_isoformat(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # -----------------------
    # PROJECT METADATA
    # -----------------------

    def get_metadata(self) -> dict:
        return self._load_state().get("project", {})

    def update_metadata(self, data: dict) -> bool:
        state = self._load_state()
        project = state.setdefault("project", {})
        project.update(data)
        return self._save_state(state)

    # -----------------------
    # ARTIFACT REGISTRY
    # -----------------------

    def list_artifacts(self) -> dict:
        return self._load_state().get("artifacts", {})

    def save_artifact(self, artifact_name: str, data: Union[str, dict]) -> bool:
        self._file_manager.set_file(self.space_name, artifact_name, data)
        state = self._load_state()
        artifacts = state.setdefault("artifacts", {})
        artifacts[artifact_name] = {"saved_at": self._current_utc_isoformat()}
        return self._save_state(state)

    def load_artifact(self, artifact_name: str) -> Union[str, dict]:
        return self._file_manager.get_file(self.space_name, artifact_name, load=True)

    # -----------------------
    # FILE OPERATIONS
    # -----------------------

    def list_files(self, recursive: bool = False) -> List[str]:
        return self._file_manager.list_files(self.space_name, recursive=recursive)

    def get_file_content(self, path: str) -> Union[str, dict]:
        return self._file_manager.get_file(self.space_name, path, load=True)

    def set_file_content(self, path: str, content: Union[str, dict]) -> bool:
        return self._file_manager.set_file(self.space_name, path, content)

    # -----------------------
    # LIFECYCLE
    # -----------------------

    def delete(self) -> bool:
        return self._space_manager.delete_space(self.space_name)

    def exists(self) -> bool:
        return self._space_manager.space_exists(self.space_name)
