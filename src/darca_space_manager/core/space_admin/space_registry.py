"""
space_registry.py

Centralized metadata registry for logical spaces.
Persists and loads metadata from disk in YAML format.
"""

import os
import threading
from typing import Dict
from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils
from darca_space_manager import config

logger = DarcaLogger(name="space_registry").get_logger()

REGISTRY_FILE = os.path.join(config.get_directories()["METADATA_DIR"], "spaces_registry.yaml")


class SpaceMetadataRegistry:
    """
    Central in-memory + on-disk registry for space metadata.
    """

    def __init__(self):
        self._lock = threading.RLock()  # 🔁 Prevent deadlocks
        self._data = self._load_registry()

    def _load_registry(self) -> Dict:
        if not os.path.exists(REGISTRY_FILE):
            logger.info("Registry file not found. Initializing new registry.")
            return {
                "spaces": {},
                "base_path": config.get_directories()["SPACE_DIR"]
            }

        try:
            logger.debug("📂 Loading registry from disk.")
            return YamlUtils.load_yaml_file(REGISTRY_FILE)
        except Exception as e:
            logger.error("❌ Failed to load registry file.", exc_info=True)
            raise RuntimeError("Failed to load space registry.") from e

    def save_registry(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
                YamlUtils.save_yaml_file(REGISTRY_FILE, self._data)
                logger.debug("💾 Registry saved.")
            except Exception as e:
                logger.error("❌ Failed to save registry file.", exc_info=True)
                raise RuntimeError("Failed to save space registry.") from e

    def get_space(self, name: str) -> dict:
        with self._lock:
            return self._data.get("spaces", {}).get(name)

    def list_spaces(self) -> list:
        with self._lock:
            return list(self._data.get("spaces", {}).values())

    def add_space(self, name: str, space_dict: dict):
        with self._lock:
            logger.debug(f"➕ Adding/updating space '{name}' in registry.")
            self._data.setdefault("spaces", {})[name] = space_dict
            self.save_registry()

    def remove_space(self, name: str):
        with self._lock:
            if name in self._data.get("spaces", {}):
                logger.debug(f"🗑️ Removing space '{name}' from registry.")
                del self._data["spaces"][name]
                self.save_registry()

    def load_registry(self) -> Dict:
        with self._lock:
            return self._data.copy()
