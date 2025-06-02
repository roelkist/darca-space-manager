# yaml_metadata_repository.py
# License: MIT

import os
import threading
from datetime import datetime, timezone
from typing import Dict, List

from darca_log_facility.logger import DarcaLogger
from darca_yaml.yaml_utils import YamlUtils
from darca_space_manager.config import get_directories
from darca_space_manager.metaspace.metaspace_backend import MetaspaceBackend

logger = DarcaLogger(name="space_registry").get_logger()

REGISTRY_FILE = os.path.join(get_directories()["METADATA_DIR"], "spaces_registry.yaml")


class YamlMetaspaceBackend(MetaspaceBackend):
    """
    YAML-based implementation of the MetaspaceBackend interface.

    Provides explicit and safe methods for managing individual space attributes.
    Thread-safe and auto-handles timestamps.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._data = self._load_registry()

    def _load_registry(self) -> Dict:
        if not os.path.exists(REGISTRY_FILE):
            logger.info("Registry file not found. Initializing new registry.")
            return {
                "spaces": {},
                "base_path": get_directories()["SPACE_DIR"]
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

    def load_registry(self) -> Dict:
        with self._lock:
            return self._data.copy()

    def get_space(self, name: str) -> dict:
        with self._lock:
            return self._data.get("spaces", {}).get(name)

    def list_spaces(self) -> List[dict]:
        with self._lock:
            return list(self._data.get("spaces", {}).values())

    # ------------------------
    # Creation
    # ------------------------

    def add_space(
        self,
        name: str,
        label: str = "",
        repository: str = "",
        owner: str = "default_user",
        permissions: List[str] = None,
    ):
        with self._lock:
            if name in self._data["spaces"]:
                logger.debug(f"🔄 Updating existing space '{name}'")
            else:
                logger.debug(f"➕ Creating new space '{name}'")
                self._data.setdefault("spaces", {})[name] = {"name": name}
                self._set_created_at_internal(name)

            if label:
                self.set_label(name, label)

            if repository:
                self.set_repository(name, repository)

            self.set_owner(name, owner)
            self.set_permissions(name, permissions or ["read", "write"])
            self.touch(name)

    def remove_space(self, name: str):
        with self._lock:
            if name in self._data["spaces"]:
                logger.debug(f"🗑️ Removing space '{name}' from registry.")
                del self._data["spaces"][name]
                self.save_registry()

    # ------------------------
    # Rename
    # ------------------------

    def rename_space(self, old_name: str, new_name: str) -> dict:
        with self._lock:
            if new_name in self._data["spaces"]:
                raise ValueError(f"Space '{new_name}' already exists.")
            if old_name not in self._data["spaces"]:
                raise ValueError(f"Space '{old_name}' does not exist.")

            space_data = self._data["spaces"].pop(old_name)
            space_data["name"] = new_name
            space_data["last_modified_at"] = datetime.now(timezone.utc).isoformat()
            self._data["spaces"][new_name] = space_data
            self.save_registry()
            return space_data

    # ------------------------
    # Field-level Setters
    # ------------------------

    def set_label(self, name: str, label: str) -> dict:
        return self._update(name, {"label": label})

    def set_repository(self, name: str, repository: str) -> dict:
        return self._update(name, {"repository": repository})

    def set_owner(self, name: str, owner: str) -> dict:
        return self._update(name, {"owner": owner})

    def set_permissions(self, name: str, permissions: List[str]) -> dict:
        return self._update(name, {"permissions": permissions})

    def set_created_at(self, name: str, timestamp: str) -> dict:
        return self._update(name, {"created_at": timestamp}, auto_touch=False)

    def set_last_modified_at(self, name: str, timestamp: str) -> dict:
        return self._update(name, {"last_modified_at": timestamp}, auto_touch=False)

    def touch(self, name: str) -> dict:
        return self._update(name, {})  # Triggers last_modified_at internally

    # ------------------------
    # Internal Logic
    # ------------------------

    def _update(self, name: str, patch: dict, auto_touch: bool = True) -> dict:
        if name not in self._data["spaces"]:
            raise ValueError(f"Space '{name}' does not exist.")

        space_data = self._data["spaces"][name]
        space_data.update(patch)

        if auto_touch:
            space_data["last_modified_at"] = datetime.now(timezone.utc).isoformat()

        self.save_registry()
        return space_data

    def _set_created_at_internal(self, name: str):
        # Only set if not already present (guarded internally)
        if "created_at" not in self._data["spaces"][name]:
            self._data["spaces"][name]["created_at"] = datetime.now(timezone.utc).isoformat()
