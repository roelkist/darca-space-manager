# yaml_backend_repository.py
# License: MIT

import os
import yaml
from typing import Dict, List

from darca_space_manager.repository.models import Repository
from darca_space_manager.repository.repository_registry import RepositoryRegistry


class YamlRepositoryRegistry(RepositoryRegistry):
    """
    Loads backend profiles from a YAML directory.
    Each YAML file represents one profile (named by its `name` field).
    """

    def __init__(self, directory: str):
        self._directory = os.path.abspath(directory)
        self._profiles: Dict[str, Repository] = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Repository]:
        profiles = {}
        if not os.path.isdir(self._directory):
            raise FileNotFoundError(f"Profile directory does not exist: {self._directory}")

        for fname in os.listdir(self._directory):
            if not fname.endswith(".yaml"):
                continue

            path = os.path.join(self._directory, fname)
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                profile = Repository(**data)
                profiles[profile.name] = profile

        return profiles

    def get_profile(self, name: str) -> Repository:
        try:
            return self._profiles[name]
        except KeyError:
            raise KeyError(f"No profile named '{name}' found in {self._directory}.")

    def list_profiles(self) -> List[Repository]:
        return list(self._profiles.values())
