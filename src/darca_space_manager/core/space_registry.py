import os
import threading
from typing import Optional, List

from darca_log_facility import DarcaLogger
from darca_yaml import YamlUtils
from darca_space_manager import config

logger = DarcaLogger(name="space_registry").get_logger()

REGISTRY_FILE = os.path.join(config.get_directories()["METADATA_DIR"], "spaces_registry.yaml")

class SpaceMetadataRegistry:
    _lock = threading.Lock()

    def __init__(self):
        self._registry = self.load_registry()

    def load_registry(self) -> dict:
        if not os.path.exists(REGISTRY_FILE):
            logger.info("Registry file not found. Initializing new registry.")
            return {"spaces": {}}
        try:
            return YamlUtils.load_yaml_file(REGISTRY_FILE)
        except Exception as e:
            logger.error("Failed to load space registry", exc_info=True)
            raise RuntimeError("Cannot load space registry") from e

    def save_registry(self):
        try:
            with self._lock:
                YamlUtils.save_yaml_file(REGISTRY_FILE, self._registry)
        except Exception as e:
            logger.error("Failed to save space registry", exc_info=True)
            raise RuntimeError("Cannot save space registry") from e

    def add_space(self, name: str, metadata: dict):
        with self._lock:
            self._registry["spaces"][name] = metadata
            self.save_registry()

    def remove_space(self, name: str):
        with self._lock:
            if name in self._registry["spaces"]:
                del self._registry["spaces"][name]
                self.save_registry()

    def get_space(self, name: str) -> Optional[dict]:
        return self._registry["spaces"].get(name)

    def list_spaces(self) -> List[dict]:
        return list(self._registry["spaces"].values())
